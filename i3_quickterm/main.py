#!/usr/bin/env python3

import argparse
import copy
import fcntl
import json
import os
import shlex
import shutil
import subprocess
import sys
import traceback

from typing import cast, Any, Dict, Generator, Literal, Optional, TextIO

from contextlib import contextmanager, suppress
from pathlib import Path

import i3ipc


__version__ = "1.2"


# fmt: off
DEFAULT_CONF = {
    "menu": "rofi -dmenu -p 'quickterm: ' -no-custom -auto-select",
    "term": "auto",
    "history": "{$HOME}/.cache/i3-quickterm/shells.order",
    "ratio": 0.25,
    "pos": "top",
    "shells": {
        "js": "node",
        "python": "ipython3 --no-banner",
        "shell": "{$SHELL}"
    }
}
# fmt: on


MARK_QT_PATTERN = "quickterm_.*"
MARK_QT = "quickterm_{}"

# types
ExecFmtMode = Literal["expanded", "string"]
Conf = Dict[str, Any]


def TERM(
    executable: str,
    execopt: str = "-e",
    execfmt: ExecFmtMode = "expanded",
    titleopt: Optional[str] = "-T",
):
    """Helper to declare a terminal in the hardcoded list"""
    if execfmt not in ("expanded", "string"):
        raise RuntimeError("Invalid execfmt")

    fmt = executable

    if titleopt is not None:
        fmt += " " + titleopt + " {title}"

    fmt += f" {execopt} {{{execfmt}}}"

    return fmt


TERMS = {
    "alacritty": TERM("alacritty", titleopt="-t"),
    "foot": TERM("foot", titleopt="-T", execopt="", execfmt="expanded"),
    "gnome-terminal": TERM("gnome-terminal", execopt="--", titleopt=None),
    "kitty": TERM("kitty", titleopt="-T"),
    "roxterm": TERM("roxterm"),
    "st": TERM("st"),
    "terminator": TERM("terminator", execopt="-x", titleopt="-T"),
    "termite": TERM("termite", execfmt="string", titleopt="-t"),
    "urxvt": TERM("urxvt"),
    "urxvtc": TERM("urxvtc"),
    "xfce4-terminal": TERM("xfce4-terminal", execfmt="string"),
    "xterm": TERM("xterm"),
}


def quoted(s: str) -> str:
    return "'" + s + "'"


def expand_command(cmd: str, **rplc_map):
    d = {"$" + k: v for k, v in os.environ.items()}
    d.update(rplc_map)

    return shlex.split(cmd.format(**d))


def term_title(shell: str) -> str:
    return f"{shell} - i3-quickterm"


def conf_path() -> Optional[str]:
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


def read_conf(fn) -> Conf:
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
def read_history_file(conf: Conf) -> Generator[Optional[TextIO], None, None]:
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


def select_terminal(term_fmt: str) -> str:
    if term_fmt == "auto":
        for t, fmt in sorted(TERMS.items()):
            if shutil.which(t) is not None:
                return fmt
        raise RuntimeError(
            f"Could not find a suitable terminal "
            f"in the predefined list: {sorted(TERMS.keys())}"
        )
    elif term_fmt in TERMS:
        # one of the pre-configured terminals
        return cast(str, TERMS.get(term_fmt))

    return term_fmt


def select_shell(conf: Conf) -> Optional[str]:
    """Select shell to use using menu application"""
    with read_history_file(conf) as hist:
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

        assert proc.stdin is not None

        for r in shells:
            proc.stdin.write((r + "\n").encode())
        stdout, _ = proc.communicate()

        shell = stdout.decode().strip()

        if len(shell) == 0:
            return None

        if shell not in conf["shells"]:
            raise RuntimeError(f"Unknown shell: {shell}")

        if hist is not None:
            # put the selected shell on top
            shells = [shell] + [s for s in shells if s != shell]
            hist.truncate(0)
            json.dump(shells, hist)

        return shell


def move_to_scratchpad(conn: i3ipc.Connection, selector: str):
    conn.command(f"{selector} floating enable, move scratchpad")


def get_current_workspace(conn: i3ipc.Connection):
    focused = conn.get_tree().find_focused()
    if not focused:
        return None
    return focused.workspace()


class VerboseConnection(i3ipc.Connection):
    def __init__(self):
        super().__init__()

    def command(self, payload: str, *kargs, **kwargs):
        print(f"command: {payload}")
        return super().command(payload, *kargs, **kwargs)


class Quickterm:
    def __init__(self, conf: Conf, shell: Optional[str]):
        self.conf = conf
        self.shell = shell
        self._ws = None
        self._ws_fetched = False
        self._conn = None
        self._con = None
        self._con_fetched = False
        self._verbose = self.conf.get("_verbose", False)

    @property
    def conn(self) -> i3ipc.Connection:
        if self._conn is None:
            if self._verbose:
                self._conn = VerboseConnection()
            else:
                self._conn = i3ipc.Connection()
        return self._conn

    @property
    def ws(self) -> Optional[i3ipc.Con]:
        if not self._ws_fetched and self._ws is None:
            self._ws = get_current_workspace(self.conn)
            self._ws_fetched = True
        return self._ws

    @property
    def mark(self) -> str:
        if self.shell is None:
            raise RuntimeError("No shell defined")
        return MARK_QT.format(self.shell)

    @property
    def con(self) -> Optional[i3ipc.Con]:
        """Find container in complete tree"""
        if not self._con_fetched and self._con is None:
            node = self.conn.get_tree().find_marked(self.mark)
            if len(node) == 0:
                self._con = None
            else:
                self._con = node[0]
            self._con_fetched = True
        return self._con

    def con_in_workspace(self, mark: str) -> Optional[i3ipc.Con]:
        """Find container in workspace"""
        if self.ws is None:
            return None
        c = self.ws.find_marked(mark)
        if len(c) == 0:
            return None
        return c[0]

    def execvp(self, cmd):
        if self._verbose:
            print(f"execvp: {cmd}")
        os.execvp(cmd[0], cmd)

    """Operations"""

    def launch_inplace(self):
        """Quickterm is called by itself

        Mark current window, move back and focus again, then run shell in current
        process
        """

        self.conn.command(f"mark {self.mark}")

        self.focus_on_current_ws()

        prog_cmd = expand_command(self.conf["shells"][self.shell])
        self.execvp(prog_cmd)

    def toggle_on_current_ws(self):
        """If on another workspace: hide, otherwise show on current"""
        move_to_scratchpad(self.conn, f"[con_id={self.con.id}]")

        if self.ws is not None and self.con.workspace().name != self.ws.name:
            self.focus_on_current_ws()

    def focus_on_current_ws(self):
        """Focus existing qt on current workspace"""
        ws = self.ws
        assert ws is not None
        ratio = self.conf["ratio"]
        pos = self.conf["pos"]

        wx, wy = ws.rect.x, ws.rect.y
        width, wheight = ws.rect.width, ws.rect.height

        height = int(wheight * ratio)
        posx = wx

        if pos == "bottom":
            margin = 6
            posy = wy + wheight - height - margin
        else:  # pos == 'top'
            posy = wy

        self.conn.command(
            f"[con_mark={self.mark}] "
            f"move scratchpad, "
            f"scratchpad show, "
            f"resize set {width} px {height} px, "
            f"move absolute position {posx}px {posy}px"
        )

    def execute_term(self):
        """Launch i3-quickterm in a new terminal"""
        term = select_terminal(self.conf["term"])
        qt_cmd = f"{sys.argv[0]} -i {self.shell}"
        if self._verbose:
            qt_cmd += " -v"
        if "_config" in self.conf:
            qt_cmd += f" -c {self.conf['_config']}"

        term_cmd = expand_command(
            term,
            title=quoted(term_title(self.shell)),
            expanded=qt_cmd,
            string=quoted(qt_cmd),
        )
        self.execvp(term_cmd)


def run_qt(qt: Quickterm, in_place: bool = False):
    """Main logic"""
    shell = qt.shell

    if in_place:
        if shell is None:
            raise RuntimeError("shell should be provided when running in place")

        # we are launched by ourselves: start a shell
        qt.launch_inplace()
        return

    if shell is None:
        c = qt.con_in_workspace(MARK_QT_PATTERN)
        if c is not None:
            # undefined shell and visible on workspace: hide
            move_to_scratchpad(qt.conn, f"[con_id={c.id}]")
            return

        # undefined shell and nothing on workspace: ask for shell selection
        shell = select_shell(qt.conf)
        if shell is None:
            return
        qt.shell = shell

    # show logic
    # if it does not exist: create
    # else: toggle on current workspace
    if qt.con is None:
        qt.execute_term()
        return

    qt.toggle_on_current_ws()


def main(argv=None):
    parser = argparse.ArgumentParser(prog="i3-quickterm")
    parser.add_argument("-i", "--in-place", dest="in_place", action="store_true")
    parser.add_argument("-v", "--verbose", dest="verbose", action="store_true")
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
    args = parser.parse_args(argv)

    conf = copy.deepcopy(DEFAULT_CONF)
    if args.config:
        conf.update(read_conf(args.config))
        conf["_config"] = args.config
    else:
        conf.update(read_conf(conf_path()))

    conf["_verbose"] = args.verbose

    if args.shell is not None and args.shell not in conf["shells"]:
        print(f"unknown shell: {args.shell}", file=sys.stderr)
        return 1

    qt = Quickterm(conf, args.shell)

    run_qt(qt, args.in_place)

    return 0


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except Exception:
        print(traceback.format_exc())
        sys.exit(1)
