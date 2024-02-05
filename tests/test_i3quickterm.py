from i3_quickterm.main import Quickterm, run_qt, DEFAULT_CONF

import i3ipc

import copy

import pytest
import unittest.mock
from unittest.mock import call, ANY


@pytest.fixture
def execvp():
    with unittest.mock.patch("os.execvp") as mock_execvp:
        yield mock_execvp


@pytest.fixture
def i3ipc_con():
    con = unittest.mock.Mock(i3ipc.Con)
    con.find_marked.return_value = [con]
    con.find_focused.return_value = con
    con.id = "0"
    ws = unittest.mock.MagicMock()
    con.workspace.return_value = ws
    ws.name = "ws"
    ws.rect = i3ipc.Rect({"x": 0, "y": 0, "height": 0, "width": 0})
    return con


@pytest.fixture
def i3ipc_connection(i3ipc_con):
    conn = unittest.mock.Mock(i3ipc.Connection)
    conn.get_tree.return_value = i3ipc_con
    return conn


@pytest.fixture
def conf(tmpdir):
    c = copy.deepcopy(DEFAULT_CONF)
    c.update(
        {
            "menu": "/bin/true",
            "shells": {"shell": "bash"},
            "verbose": True,
            "history": f"{str(tmpdir)}/shells.order",
        }
    )
    return c


@pytest.fixture
def quickterm_mock(i3ipc_connection, conf):
    qt = unittest.mock.Mock(Quickterm)
    qt.shell = None
    qt.con = None
    qt.conf = conf
    qt.conn = i3ipc_connection

    return qt


"""Test quickterm operations"""


def test_launch_inplace(i3ipc_connection, conf, execvp):
    """In place: just call the shell"""
    qt = Quickterm(conf, "shell", conn=i3ipc_connection)

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
    """Create term (when not found)"""
    i3ipc_con.find_marked.return_value = []

    qt = Quickterm(conf, "shell", conn=i3ipc_connection)

    qt.execute_term()

    execvp.assert_has_calls([call("urxvt", ANY)])


def test_toggle_hide(i3ipc_connection, conf, execvp):
    """Toggle with visible term: hide"""
    qt = Quickterm(conf, "shell", conn=i3ipc_connection)

    qt.toggle_on_current_ws()

    i3ipc_connection.command.assert_called_once_with(
        "[con_id=0] floating enable, move scratchpad"
    )
    assert execvp.call_count == 0


def test_toggle_from_other_workspace(i3ipc_connection, i3ipc_con, conf, execvp):
    """Toggle with visible term on another workspace: hide and show on current"""
    qt = Quickterm(conf, "shell", conn=i3ipc_connection)

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


"""Test logic"""


def test_run_qt_inplace_no_shell(quickterm_mock):
    with pytest.raises(RuntimeError):
        run_qt(quickterm_mock, in_place=True)


def test_run_qt_inplace(quickterm_mock):
    qt = quickterm_mock
    qt.shell = "bash"
    run_qt(qt, in_place=True)
    qt.launch_inplace.assert_called_once()


def test_run_qt_noshell_hide(quickterm_mock, i3ipc_connection, i3ipc_con):
    qt = quickterm_mock
    qt.con_in_workspace.return_value = i3ipc_con

    run_qt(qt)

    i3ipc_connection.command.assert_called_once_with(
        "[con_id=0] floating enable, move scratchpad"
    )


def test_run_qt_noshell_select_none(quickterm_mock):
    qt = quickterm_mock
    qt.con_in_workspace.return_value = None

    run_qt(qt)

    assert qt.shell is None


def test_run_qt_noshell_select_one(quickterm_mock):
    qt = quickterm_mock
    qt.con_in_workspace.return_value = None
    qt.conf["menu"] = "echo shell"

    run_qt(qt)

    assert qt.shell == "shell"


def test_run_qt_execute_shell(quickterm_mock):
    qt = quickterm_mock
    qt.shell = "bash"
    run_qt(qt)
    qt.execute_term.assert_called_once()


def test_run_qt_toggle_on_current_ws(i3ipc_con, quickterm_mock):
    qt = quickterm_mock
    qt.shell = "bash"
    qt.con = i3ipc_con
    run_qt(qt)
    qt.toggle_on_current_ws.assert_called_once()
