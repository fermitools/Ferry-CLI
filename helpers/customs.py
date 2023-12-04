import argparse
import os

from typing import Optional, Any, List, Dict
import textwrap

import toml

from abc import ABC, abstractmethod
from helpers.api import FerryAPI

class TConfig:
    def __init__(self) -> None:
        with open("config.toml", "r") as file:
            os.environ["UID"] = str(os.getuid())
            file_mapped = file.read().format_map(os.environ)
            self.config = toml.loads(file_mapped)

    def get_from(
        self,
        section: str,
        field: str,
        default: Optional[Any] = None,
        check_path: bool = False,
    ) -> Any:
        if section not in self.config:
            raise KeyError(f"Section '{section}' not in config file")
        retval = self.config[section].get(field, default)
        return (
            retval
            if not check_path or (check_path and os.path.exists(retval))
            else default
        )

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
        self.parser = FerryParser.create_from_workflow(self)
    
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
    
class FerryParser(argparse.ArgumentParser):
    """Custom ArgumentParser used for parsing Ferry's swagger.json file and custom workflows into CLI arguments and objects
    """
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        
    def set_arguments(self, params:List[Dict[str, Any]]) -> None:
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
                    method=f"{param['type']}: {req}"
                ), 
                required=param.get("required", False)
            )
    
    @staticmethod
    def create(description:str) -> 'FerryParser':
        f"""Creates a FerryParser instance.

        Args:
            description (string): Name of the FerryParser.

        Returns:
            FerryParser
        """
        return FerryParser(description=description)
    
    @staticmethod
    def create_from_workflow(workflow:Workflow) -> 'FerryParser':
        """Create a Ferry Parser Instance from a Supported Workflow

        Args:
            workflow (Workflow): Workflow subclass

        Raises:
            TypeError: Passed object must be a Workflow subclass

        Returns:
            FerryParser
        """
        if not isinstance(workflow, Workflow):
            raise TypeError("workflow must be a Workflow subclass")

        parser = FerryParser.create_subparser(name=workflow.name, description=workflow.description, method=workflow.method)
        parser.set_arguments(workflow.params)
        return parser
    
    @staticmethod
    def create_subparser(name:str, description:str, method:str="GET") -> 'FerryParser':
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
    def parse_description(name:str="Endpoint", method:str=None, description:str=None) -> str:
        description_lines = textwrap.wrap(description, width=60)
        first_line = description_lines[0]
        rest_lines = description_lines[1:]
        endpoint_description = "%s" % (name.replace("/", ""))
        
        if len("(%s)" % method) <= 49:
            method_char_count = 49 - len("(%s)" % method)
        else:
            method_char_count = 0

        endpoint_description = f"{endpoint_description:<{method_char_count}} ({method}) | {first_line}\n"
        for line in rest_lines:
            endpoint_description += f"{'':<50} | {line}\n"
        return endpoint_description

