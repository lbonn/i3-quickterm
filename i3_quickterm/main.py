#!/usr/bin/env python3

import argparse
import copy
import fcntl
import json
import os
import shlex
import subprocess
import sys
from contextlib import contextmanager, suppress
from pathlib import Path

import i3ipc

__version__ = "1.1"


# fmt: off
DEFAULT_CONF = {
    "menu": "rofi -dmenu -p 'quickterm: ' -no-custom -auto-select",
    "term": "urxvt",
    "term_command": "",
    "history": "{$HOME}/.cache/i3/i3-quickterm.order",
    "ratio": 0.25,
    "pos": "top",
    "shells": {
        "haskell": "ghci",
        "js": "node",
        "python": "ipython3 --no-banner",
        "shell": "{$SHELL}"
    }
}
# fmt: on


MARK_QT_PATTERN = "quickterm_.*"
MARK_QT = "quickterm_{}"


def TERM(executable, execopt="-e", execfmt="expanded", titleopt="-T"):
    """Helper to declare a terminal in the hardcoded list."""
    if execfmt not in ("expanded", "string"):
        raise RuntimeError("Invalid execfmt")

    fmt = ""

    if titleopt is not None:
        fmt += " " + titleopt + " {title}"

    fmt += f" {execopt} {{{execfmt}}}"

    return {"executable": executable, "args": fmt}


def GET_TERMS(conf):
    terms = {
        "alacritty": TERM("alacritty", titleopt="-t"),
        "kitty": TERM("kitty", titleopt="-T"),
        "gnome-terminal": TERM("gnome-terminal", execopt="--", titleopt=None),
        "roxterm": TERM("roxterm"),
        "st": TERM("st"),
        "termite": TERM("termite", execfmt="string", titleopt="-t"),
        "urxvt": TERM("urxvt"),
        "urxvtc": TERM("urxvtc"),
        "foot": TERM("foot", titleopt="-T", execopt="", execfmt="expanded"),
        "xfce4-terminal": TERM("xfce4-terminal", execfmt="string"),
        "xterm": TERM("xterm"),
    }
    executable_override = conf["term_command"]
    return {
        term: (
            command["executable"] if executable_override == "" else executable_override
        )
        + command["args"]
        for term, command in terms.items()
    }


def conf_path():
    locations = [
        "i3-quickterm/config.json",
        "i3/i3-quickterm.json",  # legacy location
    ]
    home_dir = os.environ["HOME"]
    xdg_dir = os.environ.get("XDG_CONFIG_DIR", f"{home_dir}/.config")

    for loc in locations:
        full_loc = f"{xdg_dir}/{loc}"
        if os.path.exists(full_loc):
            return full_loc

    return None


def read_conf(fn):
    if fn is None:
        print("no config file! using defaults", file=sys.stderr)
        return {}

    try:
        with open(fn, "r") as f:
            c = json.load(f)
        return c
    except Exception as e:
        print(f"invalid config file: {e}", file=sys.stderr)
        return {}


@contextmanager
def get_history_file(conf):
    if conf["history"] is None:
        yield None
        return

    p = Path(expand_command(conf["history"])[0])

    os.makedirs(str(p.parent), exist_ok=True)

    f = open(str(p), "a+")
    fcntl.lockf(f, fcntl.LOCK_EX)

    try:
        f.seek(0)
        yield f
    finally:
        fcntl.lockf(f, fcntl.LOCK_UN)
        f.close()


def expand_command(cmd, **rplc_map):
    d = {"$" + k: v for k, v in os.environ.items()}
    d.update(rplc_map)

    return shlex.split(cmd.format(**d))


def move_back(conn, selector):
    conn.command(f"{selector} floating enable, move scratchpad")


def pop_it(conn, mark_name, pos="top", ratio=0.25):
    ws = get_current_workspace(conn)
    wx, wy = ws.rect.x, ws.rect.y
    width, wheight = ws.rect.width, ws.rect.height

    height = int(wheight * ratio)
    posx = wx

    if pos == "bottom":
        margin = 6
        posy = wy + wheight - height - margin
    else:  # pos == 'top'
        posy = wy

    conn.command(
        f"[con_mark={mark_name}],"
        f"move scratchpad,"
        f"scratchpad show,"
        f"resize set {width} px {height} px,"
        f"move absolute position {posx}px {posy}px"
    )


def get_current_workspace(conn):
    return conn.get_tree().find_focused().workspace()


def toggle_quickterm_select(conf, hist=None):
    """Hide a quickterm visible on current workspace or prompt the user for a
    shell type."""
    conn = i3ipc.Connection()
    ws = get_current_workspace(conn)

    # is there a quickterm opened in the current workspace?
    qt = ws.find_marked(MARK_QT_PATTERN)
    if qt:
        qt = qt[0]
        move_back(conn, f"[con_id={qt.id}]")
        return

    with get_history_file(conf) as hist:
        # compute the list from conf + (maybe) history
        hist_list = None
        if hist is not None:
            with suppress(Exception):
                hist_list = json.load(hist)

                # invalidate if different set from the configured shells
                if set(hist_list) != set(conf["shells"].keys()):
                    hist_list = None

        shells = hist_list or sorted(conf["shells"].keys())

        proc = subprocess.Popen(
            expand_command(conf["menu"]), stdin=subprocess.PIPE, stdout=subprocess.PIPE
        )

        for r in shells:
            proc.stdin.write((r + "\n").encode())
        stdout, _ = proc.communicate()

        shell = stdout.decode().strip()

        if shell not in conf["shells"]:
            return

        if hist is not None:
            # put the selected shell on top
            shells = [shell] + [s for s in shells if s != shell]
            hist.truncate(0)
            json.dump(shells, hist)

    toggle_quickterm(conf, shell)


def quoted(s):
    return "'" + s + "'"


def term_title(shell):
    return f"{shell} - i3-quickterm"


def toggle_quickterm(conf, shell):
    conn = i3ipc.Connection()
    shell_mark = MARK_QT.format(shell)
    qt = conn.get_tree().find_marked(shell_mark)

    # does it exist already?
    if len(qt) == 0:
        term = GET_TERMS(conf).get(conf["term"], conf["term"])
        qt_cmd = f"{sys.argv[0]} -i {shell}"
        if "_config" in conf:
            qt_cmd += f" -c {conf['_config']}"

        term_cmd = expand_command(
            term,
            title=quoted(term_title(shell)),
            expanded=qt_cmd,
            string=quoted(qt_cmd),
        )
        os.execvp(term_cmd[0], term_cmd)
    else:
        qt = qt[0]
        ws = get_current_workspace(conn)

        move_back(conn, f"[con_id={qt.id}]")
        if qt.workspace().name != ws.name:
            pop_it(conn, shell_mark, conf["pos"], conf["ratio"])


def launch_inplace(conf, shell):
    conn = i3ipc.Connection()
    shell_mark = MARK_QT.format(shell)
    conn.command(f"mark {shell_mark}")
    move_back(conn, "f[con_mark={shell_mark}]")
    pop_it(conn, shell_mark, conf["pos"], conf["ratio"])
    prog_cmd = expand_command(conf["shells"][shell])
    os.execvp(prog_cmd[0], prog_cmd)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--in-place", dest="in_place", action="store_true")
    parser.add_argument(
        "-c",
        "--config",
        dest="config",
        type=str,
        help="read config from specified file",
    )
    parser.add_argument("shell", metavar="SHELL", nargs="?")
    parser.add_argument(
        "--version", action="version", version=f"%(prog)s {__version__}"
    )
    args = parser.parse_args()

    conf = copy.deepcopy(DEFAULT_CONF)
    if args.config:
        conf.update(read_conf(args.config))
        conf["_config"] = args.config
    else:
        conf.update(read_conf(conf_path()))

    if args.shell is None:
        toggle_quickterm_select(conf)
        sys.exit(0)

    if args.shell not in conf["shells"]:
        print(f"unknown shell: {args.shell}", file=sys.stderr)
        sys.exit(1)

    if args.in_place:
        launch_inplace(conf, args.shell)
    else:
        toggle_quickterm(conf, args.shell)


if __name__ == "__main__":
    main()
