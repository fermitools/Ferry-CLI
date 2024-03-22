from collections import namedtuple
import configparser
import enum
import json
import time
import pathlib
from typing import List

import os

import pytest

from ferry_cli.config import CONFIG_DIR, config


@pytest.fixture
def stash_xdg_config_home(stash_env):
    return stash_env("XDG_CONFIG_HOME")


@pytest.fixture
def stash_home(stash_env):
    return stash_env("HOME")


@pytest.fixture
def create_config_file_dummy():
    def inner(env_path: pathlib.Path, *path_parts_to_base_dir: List[str]) -> None:
        base_dir = env_path
        for part in path_parts_to_base_dir:
            base_dir = base_dir / part
        base_dir.mkdir(parents=True)
        path_to_file = base_dir / "config.ini"
        path_to_file.touch()

    return inner


@pytest.fixture
def test_config_template_string():
    data_dir = f"{os.path.dirname(os.path.abspath(__file__))}/data"
    template_file = pathlib.Path(f"{data_dir}/test_config_template")
    with open(template_file, "r") as f:
        s = f.read()
    return s


write_out_configfile_test_param = namedtuple(
    "write_out_configfile_test_param", ("config_vals", "file_contents")
)


def get_write_out_configfile_test_params():
    data_dir = f"{os.path.dirname(os.path.abspath(__file__))}/data"
    params_file = pathlib.Path(f"{data_dir}/write_out_configfile_template_tests")
    with open(params_file, "r") as f:
        s = f.read()
    params_list = json.loads(s)
    params = []
    for item in params_list:
        params.append(write_out_configfile_test_param(**item))
    return params


@pytest.mark.unit
def test_get_configfile_xdg_config_home_(
    stash_xdg_config_home, create_config_file_dummy, tmp_path, monkeypatch
):
    monkeypatch.delenv("XDG_CONFIG_HOME", raising=False)
    assert not config._get_configfile_path_xdg_config_home()
    env_path = tmp_path
    monkeypatch.setenv("XDG_CONFIG_HOME", env_path)
    create_config_file_dummy(env_path, "ferry_cli")

    assert config._get_configfile_path_xdg_config_home() == pathlib.Path(
        f"{env_path}/ferry_cli/config.ini"
    )


@pytest.mark.unit
def test_get_configfile_home(
    stash_home, create_config_file_dummy, tmp_path, monkeypatch
):
    monkeypatch.delenv("HOME", raising=False)
    env_path = tmp_path
    create_config_file_dummy(env_path, ".config", "ferry_cli")
    monkeypatch.setenv("HOME", env_path)

    assert config._get_configfile_path_home() == pathlib.Path(
        f"{env_path}/.config/ferry_cli/config.ini"
    )


class _expectedPathRoot(enum.Enum):
    XDG_CONFIG_HOME = 1
    HOME = 2
    NOT_FOUND = 3


configfile_test_param = namedtuple(
    "configfile_test_param",
    [
        "xdg_config_home_path",
        "home_config_path",
        "expected",
    ],
)

get_configfile_params_for_test = [
    configfile_test_param(True, True, _expectedPathRoot.XDG_CONFIG_HOME),
    configfile_test_param(True, False, _expectedPathRoot.XDG_CONFIG_HOME),
    configfile_test_param(False, True, _expectedPathRoot.HOME),
    configfile_test_param(False, False, _expectedPathRoot.NOT_FOUND),
]


@pytest.mark.parametrize(
    "param_val",
    get_configfile_params_for_test,
)
@pytest.mark.unit
def test_get_configfile_path(
    stash_xdg_config_home,
    stash_home,
    tmp_path,
    monkeypatch,
    param_val,
):
    monkeypatch.delenv("XDG_CONFIG_HOME", raising=False)
    monkeypatch.delenv("HOME", raising=False)
    xdg_path = tmp_path
    home_path = tmp_path
    if param_val.xdg_config_home_path:
        monkeypatch.setenv("XDG_CONFIG_HOME", xdg_path)
    if param_val.home_config_path:
        monkeypatch.setenv("HOME", home_path)

    if param_val.expected == _expectedPathRoot.XDG_CONFIG_HOME:
        expectedPath = xdg_path / "ferry_cli" / "config.ini"
        assert config.get_configfile_path() == expectedPath
    elif param_val.expected == _expectedPathRoot.HOME:
        expectedPath = home_path / ".config" / "ferry_cli" / "config.ini"
        assert config.get_configfile_path() == expectedPath
    else:
        assert not config.get_configfile_path()


@pytest.mark.unit
def test_get_template_path():
    assert config._get_template_path() == pathlib.Path(f"{CONFIG_DIR}/config.ini")


@pytest.mark.parametrize("param", get_write_out_configfile_test_params())
@pytest.mark.unit
def test__write_out_configfile_with_template(
    # See tests/data/write_out_configfile_tests for test cases:
    # 1. Empty values dict --> Template is not filled, key strings left
    # 2. Values dict has good keys, none missing --> tempate filled
    # 3. Values dict has good key, missing one key --> template filled with good key
    # 4. Values dict has good key and bad key --> template filled with good key, bad key ignored
    # 5. Values dict has bad keys --> template not filled, key strings left
    stash_xdg_config_home,
    monkeypatch,
    tmp_path,
    test_config_template_string,
    param,
):
    test_dir = tmp_path
    monkeypatch.setenv("XDG_CONFIG_HOME", str(test_dir.absolute()))
    cfile = config._write_out_configfile_with_template(
        param.config_vals, test_config_template_string
    )
    assert (cfile is not None) and cfile.exists()

    # Inspect file
    with open(cfile, "r") as f:
        assert f.read() == param.file_contents


@pytest.mark.unit
def test_write_out_configfile(stash_xdg_config_home, monkeypatch, tmp_path):
    test_dir = tmp_path
    monkeypatch.setenv("XDG_CONFIG_HOME", str(test_dir.absolute()))
    config_val = {"base_url": "https://hostname.domain:port"}

    cfile = config.write_out_configfile(config_val)
    assert (cfile is not None) and cfile.exists()

    # Make sure we wrote out the file correctly
    cfg = configparser.ConfigParser()
    with open(cfile, "r") as f:
        cfg.read_file(f)

    assert cfg.get("api", "base_url") == "https://hostname.domain:port"
