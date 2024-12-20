import argparse
import textwrap
from typing import Any, List, Dict


class FerryParser(argparse.ArgumentParser):
    """Custom ArgumentParser used for parsing Ferry's swagger.json file and custom workflows into CLI arguments and objects"""

    def __init__(self: "FerryParser", **kwargs) -> None:  # type: ignore
        super().__init__(**kwargs)

    def set_arguments(self, params: List[Dict[str, Any]]) -> None:
        """Initializes arguments for the parser from the

        Args:
            params (list): An array of Dictionary objects representing a parameter option
        """
        for param in params:
            req = "required" if param.get("required", False) else "optional"
            self.add_argument(
                f"--{param['name']}",
                type=str,
                help=FerryParser.parse_description(
                    name="",
                    description=param["description"],
                    method=f"{param['type']}: {req}",
                ),
                required=param.get("required", False),
            )

    @staticmethod
    def create(description: str, **kwargs: Any) -> "FerryParser":
        """Creates a FerryParser instance.

        Args:
            description (string): Name of the FerryParser.

        Returns:
            FerryParser
        """
        return FerryParser(description=description, **kwargs)

    @staticmethod
    def create_subparser(
        name: str, description: str, method: str = "GET"
    ) -> "FerryParser":
        """Create a FerryParser subparser.

        Args:
            name (str): Name of subparser
            description (str): What does this subparser do?
            method (str, optional): API Method Type. Defaults to GET.

        Returns:
            FerryParser
        """
        description = FerryParser.parse_description(name, method, description)
        return FerryParser(description=description)

    @staticmethod
    def parse_description(
        name: str = "Endpoint", method: str = "", description: str = ""
    ) -> str:
        description_lines = textwrap.wrap(description, width=60)
        first_line = description_lines[0]
        rest_lines = description_lines[1:]
        endpoint_description = name.replace("/", "")

        if len(f"({method})") <= 49:
            method_char_count = 49 - len(f"({method})")
        else:
            method_char_count = 0

        endpoint_description = (
            f"{endpoint_description:<{method_char_count}} ({method}) | {first_line}\n"
        )
        for line in rest_lines:
            endpoint_description += f"{'':<50} | {line}\n"
        return endpoint_description
