from i3_quickterm.main import main, DEFAULT_CONF

import os
import os.path

import pytest
import unittest.mock
from unittest.mock import ANY

DEFAULT_WITH_VERBOSE = {"_verbose": False}
DEFAULT_WITH_VERBOSE.update(DEFAULT_CONF)


@pytest.fixture
def run_qt_patched():
    with unittest.mock.patch("i3_quickterm.main.run_qt") as mock_qt:
        yield mock_qt


def is_config_path(path):
    if os.path.realpath(path).endswith("/i3-quickterm/config.json"):
        return True
    if os.path.realpath(path).endswith("/i3/i3-quickterm.json"):
        return True
    return False


@pytest.fixture
def system_conf():
    exists_ = os.path.exists

    def fake_exists(path):
        if is_config_path(path):
            return True
        return exists_(path)

    m = unittest.mock.MagicMock()
    m.side_effect = fake_exists
    exist_mock = unittest.mock.patch("os.path.exists", new=m)

    open_mock = unittest.mock.patch("i3_quickterm.main.open", unittest.mock.mock_open())

    jsonm = unittest.mock.MagicMock()
    json_load_mock = unittest.mock.patch("json.load", new=jsonm)

    with exist_mock, open_mock, json_load_mock:
        yield jsonm


@pytest.fixture
def system_conf_none():
    exists_ = os.path.exists

    def fake_exists(path):
        nonlocal exists_
        if is_config_path(path):
            return False
        return exists_(path)

    m = unittest.mock.MagicMock()
    m.side_effect = fake_exists
    exist_mock = unittest.mock.patch("os.path.exists", new=m)

    with exist_mock:
        yield


def test_args_version_help(capsys):
    with pytest.raises(SystemExit):
        main(["--version"])

    out, _ = capsys.readouterr()
    assert out.startswith("i3-quickterm")

    with pytest.raises(SystemExit):
        main(["--help"])

    out, _ = capsys.readouterr()
    assert out.startswith("usage: i3-quickterm")


def test_args_simple(conf, conf_file_factory, run_qt_patched):
    conf_file_factory.write(conf)

    assert main(["-c", f"{conf_file_factory.fname}"]) == 0

    run_qt_patched.assert_called_once_with(ANY, False)

    qt, _ = run_qt_patched.call_args.args
    assert not qt.conf["_verbose"]
    assert qt.conf["menu"] == "/bin/true"
    assert qt.conf["term"] == "xterm"
    assert qt.conf["shells"] == {"shell": "bash"}
    # from the defaults
    assert qt.conf["pos"] == "top"


def test_args_inplace(conf, conf_file_factory, run_qt_patched):
    conf_file_factory.write(conf)

    assert main(["-i", "-c", f"{conf_file_factory.fname}"]) == 0

    run_qt_patched.assert_called_once_with(ANY, True)


def test_args_verbose(conf, conf_file_factory, run_qt_patched):
    conf_file_factory.write(conf)

    assert main(["-v", "-c", f"{conf_file_factory.fname}"]) == 0

    run_qt_patched.assert_called_once_with(ANY, False)

    qt, _ = run_qt_patched.call_args.args
    assert qt.conf["_verbose"]


def test_args_wrong_shell(conf, conf_file_factory, run_qt_patched):
    conf_file_factory.write(conf)

    assert main(["-c", f"{conf_file_factory.fname}", "noshell"]) == 1

    assert run_qt_patched.call_count == 0


def test_args_system_conf_none(system_conf_none, run_qt_patched, capsys):
    assert main([]) == 0

    run_qt_patched.assert_called_once_with(ANY, False)

    _, err = capsys.readouterr()
    assert err.find("using defaults") != -1

    qt, _ = run_qt_patched.call_args.args
    assert qt.conf == DEFAULT_WITH_VERBOSE


def test_args_system_conf_term(system_conf, run_qt_patched):
    system_conf.return_value = {"term": "myterm"}

    assert main([]) == 0

    run_qt_patched.assert_called_once_with(ANY, False)

    qt, _ = run_qt_patched.call_args.args
    assert qt.conf["term"] == "myterm"


def test_args_system_conf_empty(system_conf, run_qt_patched):
    system_conf.return_value = {}

    assert main([]) == 0

    run_qt_patched.assert_called_once_with(ANY, False)

    qt, _ = run_qt_patched.call_args.args
    assert qt.conf == DEFAULT_WITH_VERBOSE


def test_args_system_conf_invalid(system_conf, run_qt_patched, capsys):
    system_conf.side_effect = RuntimeError("Invalid configuration")

    assert main([]) == 0

    run_qt_patched.assert_called_once_with(ANY, False)

    _, err = capsys.readouterr()
    assert err.find("invalid config") != -1

    qt, _ = run_qt_patched.call_args.args
    assert qt.conf == DEFAULT_WITH_VERBOSE
