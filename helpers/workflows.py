from abc import ABC, abstractmethod
from helpers.api import FerryAPI
from helpers.customs import FerryParser
from typing import Any, Dict, List, Optional


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
        if not self.parser:
            self.init_parser()
        self.parser.print_help()

    def get_description(self) -> None:
        if not self.parser:
            self.init_parser()
        print(self.parser.description)

    @abstractmethod
    def run(self, api, *args):  # type: ignore
        # This method should be implemented by all subclasses
        pass
