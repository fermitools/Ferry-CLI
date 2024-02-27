from collections import namedtuple
import enum
import pathlib
import importlib
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


@pytest.mark.unit
def test_get_configfile_xdg_config_home_(
    stash_xdg_config_home, create_config_file_dummy, tmp_path, monkeypatch
):
    monkeypatch.delenv("XDG_CONFIG_HOME", raising=False)
    print(os.environ.get("XDG_CONFIG_HOME"))
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
        "xdg_path_exists",
        "home_config_path",
        "home_path_exists",
        "expected",
    ],
)

get_configfile_params_for_test = [
    configfile_test_param(True, False, False, False, _expectedPathRoot.NOT_FOUND),
    configfile_test_param(True, False, True, False, _expectedPathRoot.NOT_FOUND),
    configfile_test_param(True, True, False, False, _expectedPathRoot.XDG_CONFIG_HOME),
    configfile_test_param(True, True, True, False, _expectedPathRoot.XDG_CONFIG_HOME),
    configfile_test_param(True, True, True, True, _expectedPathRoot.XDG_CONFIG_HOME),
    configfile_test_param(False, False, True, False, _expectedPathRoot.NOT_FOUND),
    configfile_test_param(False, False, True, True, _expectedPathRoot.HOME),
    configfile_test_param(False, False, False, False, _expectedPathRoot.NOT_FOUND),
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
    create_config_file_dummy,
    param_val,
):
    xdg_path = tmp_path
    home_path = tmp_path
    monkeypatch.setenv("XDG_CONFIG_HOME", xdg_path)
    monkeypatch.setenv("HOME", home_path)

    if param_val.xdg_path_exists:
        create_config_file_dummy(xdg_path, "ferry_cli")

    if param_val.home_path_exists:
        create_config_file_dummy(xdg_path, ".config", "ferry_cli")

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


@pytest.mark.parametrize(
    "config_exists",
    [(True), (False)],
)
@pytest.mark.unit
def test_create_configfile_if_not_exists(
    stash_xdg_config_home,
    tmp_path,
    monkeypatch,
    create_config_file_dummy,
    config_exists,
):
    env_path = tmp_path
    monkeypatch.setenv("XDG_CONFIG_HOME", env_path)

    if config_exists:
        create_config_file_dummy(env_path, "ferry_cli")
    else:
        basepath = env_path / "ferry_cli"
        basepath.mkdir()

    config.create_configfile_if_not_exists()
    assert config.get_configfile_path().exists()


@pytest.mark.parametrize(
    "mockFn,expected", [(lambda: None, False), (lambda: pathlib.Path("/"), True)]
)
@pytest.mark.unit
def test_configfile_exists(monkeypatch, mockFn, expected):
    # Since all we care about in this test is that the return value of get_configfile_path
    # is used appropriately, mock that return value to make the test simple
    monkeypatch.setattr(config, "get_configfile_path", mockFn)
    assert config.configfile_exists() == expected
