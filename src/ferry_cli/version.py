import sys
import argparse
import json
import os
from typing import Optional

try:
    from ferry_cli.config import CONFIG_DIR
except ImportError:
    from config import CONFIG_DIR  # type: ignore

__title__ = "Ferry CLI"
__swagger_file_title__ = "Ferry API"
__summary__ = "A command line interface for making ferry api calls. Can be used to automate repetitive tasks, incorporate usage safeguards for users or groups, or create scripts for common sequences. ."
__uri__ = "https://github.com/fermitools/Ferry-CLI"
__version__ = "1.1.0"
__email__ = "ltrestka@fnal.gov, sbhat@fnal.gov, brynmool@fnal.gov"
__author__ = "Fermi National Accelerator Laboratory"
__copyright__ = f"2024 {__author__}"


def get_summary() -> str:
    return __summary__


def print_version(full: bool = False, short: bool = False) -> Optional[str]:
    file_version = None
    if os.path.exists(f"{CONFIG_DIR}/swagger.json"):
        with open(f"{CONFIG_DIR}/swagger.json", "r") as file:
            json_file = json.load(file)
            file_version = json_file.get("info", {}).get("version", None)
    if short:
        return __version__
    print(f"{__title__} version {__version__}")
    if file_version and full:
        print(f"Interfacing with {__swagger_file_title__} version {file_version}")
    sys.exit()


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
