import os
import pathlib
from typing import Optional, Dict

try:
    from ferry_cli.config import CONFIG_DIR
except ImportError:
    from config import CONFIG_DIR  # type: ignore

__config_path_post_basedir = pathlib.Path("ferry_cli/config.ini")


# def create_configfile_if_not_exists() -> None:
#     # Creates a copy of the configuration template in ${XDG_CONFIG_HOME}/ferry_cli/config.ini,
#     # or ${HOME}/.config/ferry_cli/config.ini if $XDG_CONFIG_HOME is not set.
#     # If $HOME is not set for some reason, this raises an OSError
#     if configfile_exists():
#         return

#     dest_path: Optional[pathlib.Path]
#     xdg_path = _get_configfile_path_xdg_config_home()
#     home_path = _get_configfile_path_home()
#     dest_path = xdg_path if xdg_path else home_path
#     if dest_path:
#         dest_path.parent.mkdir(parents=True, exist_ok=True)
#         shutil.copy(_get_template_path(), dest_path)
#         print(f"Configuration file created at {dest_path.absolute()}")
#         return
#     raise OSError(
#         "XDG_CONFIG_HOME or HOME needs to be set to copy the template config file into place"
#     )


def get_configfile_path() -> Optional[pathlib.Path]:
    """
    Return the location of the configfile.  If $XDG_CONFIG_HOME is set,
    its value is used as the root for the config file path.  Otherwise,
    $HOME/.config is used.  If for some reason $HOME is not set,
    this function will return None.

    Equivalent to the shell call
    echo ${XDG_CONFIG_HOME:-HOME/.config}/ferry_cli/config.ini

    Note that this call does NOT guarantee that the file actually exists at the returned path.
    That should be ascertained by checking the return value against None, and then
    using the pathlib.Path.exists() method
    """

    # TODO:  Once SL7 EOL has passed, change these into assignment expressions. # pylint: disable=fixme
    # e.g. if (xdg_path := _get_configfile_path_xdg_config_home()): return xdg_path
    xdg_path = _get_configfile_path_xdg_config_home()
    if xdg_path:
        return xdg_path

    home_path = _get_configfile_path_home()
    if home_path:
        return home_path

    return None


# pylint:disable=unused-argument
def write_out_configfile(config_values: Dict[str, str]) -> pathlib.Path:
    return pathlib.Path()


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
