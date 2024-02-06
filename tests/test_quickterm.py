from i3_quickterm.main import Quickterm

import i3ipc

import pytest
import unittest.mock
from unittest.mock import call, ANY


@pytest.fixture
def execvp():
    with unittest.mock.patch("os.execvp") as mock_execvp:
        yield mock_execvp


@pytest.fixture
def shutil_roxterm_only():
    def roxterm_which(p):
        if p == "roxterm":
            return "/usr/bin/roxterm"
        return None

    with unittest.mock.patch("shutil.which", wraps=roxterm_which) as mock_execvp:
        yield mock_execvp


"""Test quickterm operations"""


def test_launch_inplace(i3ipc_connection, conf, execvp):
    """In place: just call the shell"""
    qt = Quickterm(conf, "shell")

    qt.launch_inplace()

    i3ipc_connection.command.assert_has_calls(
        [
            call("mark quickterm_shell"),
            call(
                "[con_mark=quickterm_shell] move scratchpad, scratchpad show, "
                "resize set 0 px 0 px, move absolute position 0px 0px"
            ),
        ]
    )
    execvp.assert_called_once_with("bash", ["bash"])


def test_execute_term(i3ipc_connection, i3ipc_con, conf, execvp):
    """Create term"""
    i3ipc_con.find_marked.return_value = []

    qt = Quickterm(conf, "shell")

    qt.execute_term()

    execvp.assert_has_calls([call("xterm", ANY)])


def test_execute_term_auto(
    i3ipc_connection, i3ipc_con, conf, execvp, shutil_roxterm_only
):
    """Auto-detect and execute term"""
    conf["term"] = "auto"
    i3ipc_con.find_marked.return_value = []

    qt = Quickterm(conf, "shell")

    qt.execute_term()

    execvp.assert_has_calls([call("roxterm", ANY)])


def test_execute_term_custom_format(
    i3ipc_connection, i3ipc_con, conf, execvp, shutil_roxterm_only
):
    """Auto-detect and execute term"""
    conf["term"] = "roxterm -t {title} -e {expanded}"
    i3ipc_con.find_marked.return_value = []

    qt = Quickterm(conf, "shell")

    qt.execute_term()

    execvp.assert_has_calls([call("roxterm", ANY)])


def test_execute_term_config(
    i3ipc_connection, i3ipc_con, conf, execvp, shutil_roxterm_only
):
    """Auto-detect and execute term"""
    conf["term"] = "auto"
    conf["_config"] = "dummy"
    i3ipc_con.find_marked.return_value = []

    qt = Quickterm(conf, "shell")

    qt.execute_term()

    execvp.assert_has_calls([call("roxterm", ANY)])


def test_toggle_hide(i3ipc_connection, conf, execvp):
    """Toggle with visible term: hide"""
    qt = Quickterm(conf, "shell")

    qt.toggle_on_current_ws()

    i3ipc_connection.command.assert_called_once_with(
        "[con_id=0] floating enable, move scratchpad"
    )
    assert execvp.call_count == 0


def test_con_in_workspace(i3ipc_connection, i3ipc_con, i3ipc_workspace, conf):
    qt = Quickterm(conf, None)

    assert qt.con_in_workspace("") is not None

    i3ipc_workspace.find_marked.return_value = []

    assert qt.con_in_workspace("") is None


def test_toggle_from_other_workspace(i3ipc_connection, i3ipc_con, conf, execvp):
    """Toggle with visible term on another workspace: hide and show on current"""
    qt = Quickterm(conf, "shell")

    k = 0

    def new_workspace():
        nonlocal k
        ws = unittest.mock.MagicMock()
        ws.name = f"ws{k}"
        ws.rect = i3ipc.Rect({"x": 0, "y": 0, "height": 0, "width": 0})
        k += 1
        return ws

    i3ipc_con.workspace.side_effect = new_workspace

    qt.toggle_on_current_ws()

    i3ipc_connection.command.assert_has_calls(
        [
            call("[con_id=0] floating enable, move scratchpad"),
            call(
                "[con_mark=quickterm_shell] move scratchpad, scratchpad show, "
                "resize set 0 px 0 px, move absolute position 0px 0px"
            ),
        ]
    )
    assert execvp.call_count == 0
