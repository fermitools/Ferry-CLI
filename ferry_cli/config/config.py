import os
import pathlib
import shutil
from typing import Optional

try:
    from ferry_cli.config import CONFIG_DIR
except ImportError:
    from config import CONFIG_DIR  # type: ignore

__config_path_post_basedir = pathlib.Path("ferry_cli/config.ini")


def create_configfile_if_not_exists() -> None:
    # Creates a copy of the configuration template in ${XDG_CONFIG_HOME}/ferry_cli/config.ini,
    # or ${HOME}/.config/ferry_cli/config.ini if $XDG_CONFIG_HOME is not set.
    # If $HOME is not set for some reason, this raises an OSError
    if configfile_exists():
        return

    dest_path: Optional[pathlib.Path]
    xdg_path = _get_configfile_path_xdg_config_home()
    home_path = _get_configfile_path_home()
    dest_path = xdg_path if xdg_path else home_path
    if dest_path:
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(_get_template_path(), dest_path)
        print(f"Configuration file created at {dest_path.absolute()}")
        return
    raise OSError(
        "XDG_CONFIG_HOME or HOME needs to be set to copy the template config file into place"
    )


def configfile_exists() -> bool:
    # A helper function to bridge get_configfile_path() to simply query if the configfile exists
    return get_configfile_path() is not None


def get_configfile_path() -> Optional[pathlib.Path]:
    # Try $XDG_CONFIG_HOME/ferry_cli, then $HOME/.config/ferry_cli to
    # find config.ini, and return the pathlib.Path pointing to the config file.
    # If neither directory has config.ini, return None to indicate that the config
    # file doesn't exist
    xdg_path = _get_configfile_path_xdg_config_home()
    if xdg_path and xdg_path.exists():
        return xdg_path

    home_path = _get_configfile_path_home()
    if home_path and home_path.exists():
        return home_path

    return None


def _get_configfile_path_xdg_config_home() -> Optional[pathlib.Path]:
    xdg_config_home_val = os.getenv("XDG_CONFIG_HOME")
    if not xdg_config_home_val:
        return None
    return pathlib.Path(xdg_config_home_val) / __config_path_post_basedir


def _get_configfile_path_home() -> Optional[pathlib.Path]:
    home = os.getenv("HOME")
    if not home:
        return None
    return pathlib.Path(home) / ".config" / __config_path_post_basedir


def _get_template_path() -> pathlib.Path:
    return pathlib.Path(CONFIG_DIR) / "config.ini"
