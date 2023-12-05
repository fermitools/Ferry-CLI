from abc import ABC, abstractmethod
from helpers.api import FerryAPI
from helpers.customs import FerryParser
from typing import Any

class Workflow(ABC):
    """Abstracted Workflow object that as the baseline for our custom workflows
    """
    def __init__(self, supported_workflow:'Workflow' = None) -> 'Workflow':
        self.name = supported_workflow.name if supported_workflow else None
        self.description = supported_workflow.description if supported_workflow else None
        self.method = supported_workflow.method if supported_workflow else None
        self.params = supported_workflow.params if supported_workflow else None
        self.parser = None
        
    def init_parser(self) -> None:
        self.parser = FerryParser.create_subparser(name=self.name, description=self.description, method=self.method)
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
    def run(self, api:FerryAPI, *args) -> Any:
        # This method should be implemented by all subclasses
        pass