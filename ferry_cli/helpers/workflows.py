from abc import ABC, abstractmethod
from typing import Any, Dict, List

try:
    from ferry_cli.helpers.api import FerryAPI  # pylint: disable=unused-import
    from ferry_cli.helpers.customs import FerryParser
except ImportError:
    from helpers.api import FerryAPI  # type: ignore # pylint: disable=unused-import
    from helpers.customs import FerryParser  # type: ignore


class Workflow(ABC):
    """Abstracted Workflow object that as the baseline for our custom workflows"""

    def __init__(self) -> None:
        self.name: str
        self.description: str
        self.method: str
        self.params: List[Dict[str, Any]]
        self.init_parser()

    def init_parser(self) -> None:
        self.parser = FerryParser.create_subparser(
            name=self.name, description=self.description, method=self.method
        )
        self.parser.set_arguments(self.params)

    def get_info(self) -> None:
        self.parser.print_help()

    def get_description(self) -> None:
        print(self.parser.description)

    @abstractmethod
    def run(self, api, *args):  # type: ignore
        # This method should be implemented by all subclasses
        pass

    def verify_output(self: "Workflow", api: "FerryAPI", response: Any) -> Any:
        if api.dryrun:
            return {}
        if not response:
            print("Failed to verify output")
            raise RuntimeError("Empty response from FERRY")
        if response.get("ferry_status", "") != "success":
            print("Failed to verify output")
            print(f"{response}")
            if "ferry_error" in response:
                raise RuntimeError(
                    "FERRY returned error(s): " + ", ".join(response["ferry_error"])
                )
            raise RuntimeError("FERRY did not return a successful response")
        return response["ferry_output"]
