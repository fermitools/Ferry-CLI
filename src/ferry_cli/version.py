import argparse
import configparser
from importlib.metadata import version
import json
import sys
from typing import Optional

try:
    from ferry_cli.config.config import (
        get_configfile_path,
        get_configfile_dir,
        swagger_filename,
    )
except ImportError:
    from config.config import get_configfile_path, get_configfile_dir, swagger_filename  # type: ignore

__title__ = "Ferry CLI"
__swagger_file_title__ = "Ferry API"
__summary__ = "A command line interface for making ferry api calls. Can be used to automate repetitive tasks, incorporate usage safeguards for users or groups, or create scripts for common sequences."
__uri__ = "https://github.com/fermitools/Ferry-CLI"
__version__ = version("ferry_cli")
__email__ = "ltrestka@fnal.gov, sbhat@fnal.gov, brynmool@fnal.gov"
__author__ = "Fermi National Accelerator Laboratory"
__copyright__ = f"2024 {__author__}"


def get_summary() -> str:
    return __summary__


def print_version(full: bool = False, short: bool = False) -> Optional[str]:
    if short:
        return __version__
    print(f"{__title__} version {__version__}")

    try:
        config_path = get_configfile_path()
        assert config_path is not None

        configs = configparser.ConfigParser()
        with open(config_path, "r") as f:
            configs.read_file(f)

        base_url = configs.get("api", "base_url", fallback="").strip(' "') or None
        if base_url is None:
            raise ValueError(
                f"api.base_url must be specified in the config file at {config_path}. "
                "Please set that value and try again."
            )
        swagger_endpoint = (
            configs.get("api", "swagger_file_endpoint", fallback="").strip(' "') or None
        )

        config_dir = get_configfile_dir()
        assert config_dir is not None

        _swagger_filename_kwargs = {"base_url": base_url}
        if swagger_endpoint:
            _swagger_filename_kwargs.update({"swagger_endpoint": swagger_endpoint})
        swagger_file = swagger_filename(**_swagger_filename_kwargs)

        with open(swagger_file, "r") as file:
            json_file = json.load(file)
            file_version = json_file.get("info", {}).get("version", None)
        if file_version and full:
            print(f"Interfacing with {__swagger_file_title__} version {file_version}")

    except Exception as e:  # pylint: disable=broad-except
        print(f"Error getting FERRY server version: {e}")
        sys.exit(1)

    sys.exit(0)


def print_support_email() -> None:
    print(f"Email {__email__} for help.")
    sys.exit()


def request_project_info(view: str):  # type: ignore
    class _WorkflowParams(argparse.Action):
        def __call__(  # type: ignore
            self: "_WorkflowParams", parser, args, values, option_string=None
        ) -> None:
            try:
                if view == "email":
                    print_support_email()
                elif view == "version":
                    print_version(True)
            except KeyError:
                # pylint: disable=raise-missing-from
                raise KeyError(f"Error: '{view}' is not a supported.")

    return _WorkflowParams
