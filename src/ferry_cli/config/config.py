import os
import pathlib
from typing import Optional, Dict

try:
    from ferry_cli.config import CONFIG_DIR
except ImportError:
    from config import CONFIG_DIR  # type: ignore

__config_path_post_basedir = pathlib.Path("ferry_cli/config.ini")


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


def write_out_configfile(config_values: Dict[str, str]) -> pathlib.Path:
    with open(_get_template_path(), "r") as f:
        config_template_string = f.read()
    return _write_out_configfile_with_template(config_values, config_template_string)


def _write_out_configfile_with_template(
    config_values: Dict[str, str], template_string: str
) -> pathlib.Path:
    class SafeDict(dict):  # type: ignore
        """Use this object to allow us to not need all keys of dict when
        running str.format_map method to do string interpolation.
        Taken from https://stackoverflow.com/a/17215533"""

        def __missing__(self, key: str) -> str:
            """missing item handler"""
            return f"{{{key}}}"  # "{<key>}"

    out_string = template_string.format_map(SafeDict(config_values))
    config_file_path = get_configfile_path()
    if config_file_path is None:
        raise OSError(
            "XDG_CONFIG_HOME or HOME needs to be set in order to write out the configuration file."
        )
    config_file_path.parent.mkdir(parents=True, exist_ok=True)
    print(f"Writing configuration file to {str(config_file_path)}")
    with open(config_file_path, "w") as f:
        f.write(out_string)
    return config_file_path


def _get_template_path() -> pathlib.Path:
    return pathlib.Path(CONFIG_DIR) / "config.ini"
