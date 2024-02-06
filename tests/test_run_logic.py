from i3_quickterm.main import run_qt

import pytest


"""Test run logic"""


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
