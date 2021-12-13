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


__version__ = "1.0"


# fmt: off
DEFAULT_CONF = {
    "menu": "rofi -dmenu -p 'quickterm: ' -no-custom -auto-select",
    "term": "urxvt",
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
    """Helper to declare a terminal in the hardcoded list"""
    if execfmt not in ("expanded", "string"):
        raise RuntimeError("Invalid execfmt")

    fmt = executable

    if titleopt is not None:
        fmt += " " + titleopt + " {title}"

    fmt += " {} {{{}}}".format(execopt, execfmt)

    return fmt


TERMS = {
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


def conf_path():
    home_dir = os.environ["HOME"]
    xdg_dir = os.environ.get("XDG_CONFIG_DIR", "{}/.config".format(home_dir))

    return xdg_dir + "/i3/i3-quickterm.json"


def read_conf(fn):
    try:
        with open(fn, "r") as f:
            c = json.load(f)
        return c
    except Exception as e:
        print("invalid config file: {}".format(e), file=sys.stderr)
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
    conn.command("{} floating enable, move scratchpad".format(selector))


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
        "[con_mark={mark}],"
        "move scratchpad,"
        "scratchpad show,"
        "resize set {width} px {height} px,"
        "move absolute position {posx}px {posy}px"
        "".format(mark=mark_name, posx=posx, posy=posy, width=width, height=height)
    )


def get_current_workspace(conn):
    return conn.get_tree().find_focused().workspace()


def toggle_quickterm_select(conf, hist=None):
    """Hide a quickterm visible on current workspace or prompt
    the user for a shell type"""
    conn = i3ipc.Connection()
    ws = get_current_workspace(conn)

    # is there a quickterm opened in the current workspace?
    qt = ws.find_marked(MARK_QT_PATTERN)
    if qt:
        qt = qt[0]
        move_back(conn, "[con_id={}]".format(qt.id))
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
    return "{} - i3-quickterm".format(shell)


def toggle_quickterm(conf, shell):
    conn = i3ipc.Connection()
    shell_mark = MARK_QT.format(shell)
    qt = conn.get_tree().find_marked(shell_mark)

    # does it exist already?
    if len(qt) == 0:
        term = TERMS.get(conf["term"], conf["term"])
        qt_cmd = "{} -i {}".format(sys.argv[0], shell)

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

        move_back(conn, "[con_id={}]".format(qt.id))
        if qt.workspace().name != ws.name:
            pop_it(conn, shell_mark, conf["pos"], conf["ratio"])


def launch_inplace(conf, shell):
    conn = i3ipc.Connection()
    shell_mark = MARK_QT.format(shell)
    conn.command("mark {}".format(shell_mark))
    move_back(conn, "[con_mark={}]".format(shell_mark))
    pop_it(conn, shell_mark, conf["pos"], conf["ratio"])
    prog_cmd = expand_command(conf["shells"][shell])
    os.execvp(prog_cmd[0], prog_cmd)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--in-place", dest="in_place", action="store_true")
    parser.add_argument("shell", metavar="SHELL", nargs="?")
    parser.add_argument(
        "--version", action="version", version="%(prog)s {}".format(__version__)
    )
    args = parser.parse_args()

    conf = copy.deepcopy(DEFAULT_CONF)
    conf.update(read_conf(conf_path()))

    if args.shell is None:
        toggle_quickterm_select(conf)
        sys.exit(0)

    if args.shell not in conf["shells"]:
        print("unknown shell: {}".format(args.shell), file=sys.stderr)
        sys.exit(1)

    if args.in_place:
        launch_inplace(conf, args.shell)
    else:
        toggle_quickterm(conf, args.shell)


if __name__ == "__main__":
    main()
