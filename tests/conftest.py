from i3_quickterm.main import Quickterm, DEFAULT_CONF

import i3ipc

import copy
import json

import pytest
import unittest.mock


@pytest.fixture
def conf(tmp_path):
    c = copy.deepcopy(DEFAULT_CONF)
    c.update(
        {
            "menu": "/bin/true",
            "term": "xterm",
            "shells": {"shell": "bash"},
            "history": f"{str(tmp_path / 'shells.order')}",
        }
    )
    return c


@pytest.fixture
def conf_file_factory(tmp_path):
    fname = tmp_path / "i3-quickterm.conf"

    class Fact:
        def __init__(self, fname):
            self.fname = fname

        def write(self, conf):
            with open(self.fname, "w") as f:
                json.dump(conf, f)

    return Fact(fname)


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
    with unittest.mock.patch("i3ipc.Connection") as cm:
        cm.return_value = conn
        yield conn


@pytest.fixture
def quickterm_mock(i3ipc_connection, conf):
    qt = unittest.mock.Mock(Quickterm)
    qt.shell = None
    qt.con = None
    qt.conf = conf
    qt.conn = i3ipc_connection

    return qt
