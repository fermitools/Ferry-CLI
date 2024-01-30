import argparse
import json
import os
import sys
import textwrap
from typing import Any, Dict, Optional, List, Tuple

from helpers.api import FerryAPI
from helpers.auth import (
    Auth,
    get_auth_args,
    set_auth_from_args,
    get_auth_parser,
)
from helpers.customs import TConfig, FerryParser
from helpers.supported_workflows import SUPPORTED_WORKFLOWS
from safeguards.dcs import SafeguardsDCS


def get_default_paths(config: TConfig) -> Tuple[str, str]:
    cert = config.get_from("Auth", "default_cert_path", check_path=True)
    capath = config.get_from("Auth", "default_capath", check_path=True)
    return cert, capath


class FerryCLI:
    def __init__(self: "FerryCLI") -> None:
        self.config = TConfig()
        self.base_url = self.config.get_from("Ferry", "base_url")
        self.safeguards = SafeguardsDCS()
        self.endpoints: Dict[str, Any] = {}
        self.authorizer: Optional["Auth"] = None
        self.ferry_api: Optional["FerryAPI"] = None
        self.parser: Optional["FerryParser"] = None

    def get_arg_parser(self: "FerryCLI") -> FerryParser:
        parser = FerryParser.create(
            description="CLI for Ferry API endpoints", parents=[get_auth_parser()]
        )
        parser.add_argument(
            "--filter",
            default=None,
            help="(string) Use to filter results on -le and -lw flags",
        )
        parser.add_argument(
            "-le",
            "--list_endpoints",
            action=self.list_available_endpoints_action(),
            nargs=0,
            help="List all available endpoints",
        )
        parser.add_argument(
            "-lw",
            "--list_workflows",
            action=self.list_workflows_action(),  # type: ignore
            nargs=0,
            help="List all supported custom workflows",
        )
        parser.add_argument(
            "-ep",
            "--endpoint_params",
            action=self.get_endpoint_params_action(),  # type: ignore
            help="List parameters for the selected endpoint",
        )
        parser.add_argument(
            "-wp",
            "--workflow_params",
            action=self.workflow_params_action(),  # type: ignore
            help="List parameters for the supported workflow",
        )
        parser.add_argument("-e", "--endpoint", help="API endpoint and parameters")
        parser.add_argument("-w", "--workflow", help="Execute supported workflows")
        return parser

    def list_available_endpoints_action(self: "FerryCLI"):  # type: ignore
        endpoints = self.endpoints

        class _ListEndpoints(argparse.Action):
            def __call__(  # type: ignore
                self: "_ListEndpoints", parser, args, values, option_string=None
            ) -> None:
                filter_args = FerryCLI.get_filter_args()
                print(
                    f"""
                      Listing all supported endpoints{' (filtering for "%s")' % (filter_args.filter) if filter_args.filter else ''}:
                      """
                )
                for ep, subparser in endpoints.items():
                    if filter_args.filter:
                        if filter_args.filter.lower() in ep.lower():
                            print(subparser.description)
                    else:
                        print(subparser.description)
                sys.exit(0)

        return _ListEndpoints

    def get_filter_args() -> argparse.Namespace:
        filter_parser = FerryParser()
        filter_parser.set_arguments([{
            "name": "filter",
            "description": "Filter by workflow title (contains)",
            "type": "string",
            "required":False
        }])
        filter_args, _ = filter_parser.parse_known_args()
        return filter_args
    
    def list_workflows_action(self):  # type: ignore
        class _ListWorkflows(argparse.Action):
            def __call__(  # type: ignore
                self: "_ListWorkflows", parser, args, values, option_string=None
            ) -> None:
                filter_args = FerryCLI.get_filter_args()
                print(
                    f"""
                      Listing all supported workflows{' (filtering for "%s")' % (filter_args.filter) if filter_args.filter else ''}:
                      """
                )
                for name, workflow in SUPPORTED_WORKFLOWS.items():
                    if filter_args.filter:
                        if filter_args.filter.lower() in name.lower():
                            workflow().get_description()
                    else:
                        workflow().get_description()

                sys.exit(0)

        return _ListWorkflows

    def get_endpoint_params_action(self):  # type: ignore
        safeguards = self.safeguards
        ferrycli_get_endpoint_params = self.get_endpoint_params

        class _GetEndpointParams(argparse.Action):
            def __call__(  # type: ignore
                self: "_GetEndpointParams", parser, args, values, option_string=None
            ) -> None:
                # Prevent DCS from running this endpoint if necessary, and print proper steps to take instead.
                safeguards.verify(values)
                ferrycli_get_endpoint_params(values)
                sys.exit(0)

        return _GetEndpointParams

    def workflow_params_action(self):  # type: ignore
        class _WorkflowParams(argparse.Action):
            def __call__(  # type: ignore
                self: "_WorkflowParams", parser, args, values, option_string=None
            ) -> None:
                try:
                    # Finds workflow inherited class in dictionary if exists, and initializes it.
                    workflow = SUPPORTED_WORKFLOWS[values]()
                    workflow.init_parser()
                    workflow.get_info()
                    sys.exit(0)
                except KeyError:
                    # pylint: disable=raise-missing-from
                    raise KeyError(f"Error: '{values}' is not a supported workflow.")

        return _WorkflowParams

    def get_endpoint_params(self: "FerryCLI", endpoint: str) -> None:
        # pylint: disable=consider-using-f-string
        print(
            """
              Listing parameters for endpoint: %s%s"
              """
            % (self.base_url, endpoint)
        )
        subparser = self.endpoints.get(endpoint, None)
        if not subparser:
            print(
                # pylint: disable=consider-using-f-string
                """
                  Error: '%s' is not a valid endpoint. Run 'ferry -l' for a full list of available endpoints.
                  """
                % endpoint
            )
        else:
            print(subparser.format_help())
            print()

    def execute_endpoint(self: "FerryCLI", endpoint: str, params: List[str]) -> Any:
        try:
            subparser = self.endpoints[endpoint]
        except KeyError:
            raise ValueError(  # pylint: disable=raise-missing-from
                f"Error: '{endpoint}' is not a valid endpoint. Run 'ferry -l' for a full list of available endpoints."
            )
        else:
            params_args, _ = subparser.parse_known_args(params)
            return self.ferry_api.call_endpoint(endpoint, params=vars(params_args))  # type: ignore

    def generate_endpoints(self: "FerryCLI") -> Dict[str, FerryParser]:
        endpoints = {}
        with open("config/swagger.json", "r") as json_file:

            api_data = json.load(json_file)
            for path, data in api_data["paths"].items():
                endpoint = path.replace("/", "")
                if "get" in data:
                    method = "get"
                elif "post" in data:
                    method = "post"
                elif "put" in data:
                    method = "put"

                endpoint_parser = FerryParser.create_subparser(
                    endpoint,
                    method=method.upper(),
                    description=data[method]["description"],
                )
                endpoint_parser.set_arguments(data[method].get("parameters", []))
                endpoints[path.replace("/", "")] = endpoint_parser

        return endpoints

    def parse_description(
        self: "FerryCLI", name: str, desc: str, method: Optional[str] = None
    ) -> str:
        description_lines = textwrap.wrap(desc, width=60)
        first_line = description_lines[0]
        rest_lines = description_lines[1:]
        endpoint_description = name.replace("/", "")
        method_char_count = 49 - len(f"({method})")
        endpoint_description = (
            f"{endpoint_description:<{method_char_count}} ({method}) | {first_line}\n"
        )
        for line in rest_lines:
            endpoint_description += f"{'':<50} | {line}\n"
        return endpoint_description

    def run(self: "FerryCLI", debug: bool, quiet: bool, extra_args: Any) -> None:
        self.parser = self.get_arg_parser()
        args, endpoint_args = self.parser.parse_known_args(extra_args)

        if debug:
            print(f"Args:  {vars(args)}\n" f"Endpoint Args:  {endpoint_args}")

        if not self.ferry_api:
            self.ferry_api = FerryAPI(
                base_url=self.base_url, authorizer=self.authorizer, quiet=quiet  # type: ignore
            )

        if args.endpoint:
            # Prevent DCS from running this endpoint if necessary, and print proper steps to take instead.
            self.safeguards.verify(args.endpoint)
            try:
                json_result = self.execute_endpoint(args.endpoint, endpoint_args)
            except Exception as e:
                raise Exception(f"{e}")
            if not quiet:
                self.handle_output(json.dumps(json_result, indent=4))

        elif args.workflow:
            try:
                # Finds workflow inherited class in dictionary if exists, and initializes it.
                workflow = SUPPORTED_WORKFLOWS[args.workflow]()
                workflow.init_parser()
                workflow_params, _ = workflow.parser.parse_known_args(endpoint_args)
                json_result = workflow.run(self.ferry_api, vars(workflow_params))  # type: ignore
                if not quiet:
                    self.handle_output(json.dumps(json_result, indent=4))
            except KeyError:
                raise KeyError(f"Error: '{args.workflow}' is not a supported workflow.")

        else:
            self.parser.print_help()

    # TBD if we will use this at all
    def handle_output(self: "FerryCLI", output: str) -> None:
        # Don't print excessively long responses - just store them in the result.json file and point to it.
        if len(output) < 1000:
            print(f"Response: {output}")
        else:
            with open("result.json", "w") as file:
                file.write(output)
            print(
                f"\nResponse in file: {os.path.abspath(os.environ.get('PWD', ''))}/result.json"
            )


def main() -> None:
    ferry_cli = FerryCLI()
    try:
        auth_args, other_args = get_auth_args()
        if not other_args or ("-h" in other_args) or ("--help" in other_args):
            ferry_cli.get_arg_parser().print_help()
            sys.exit(0)
        ferry_cli.authorizer = set_auth_from_args(auth_args)
        if auth_args.update or not os.path.exists("config/swagger.json"):
            print("Fetching latest swagger file...")
            ferry_cli.ferry_api = FerryAPI(
                ferry_cli.base_url, ferry_cli.authorizer, auth_args.quiet
            )
            ferry_cli.ferry_api.get_latest_swagger_file()
            print("Successfully stored latest swagger file.\n")

        ferry_cli.endpoints = ferry_cli.generate_endpoints()
        ferry_cli.run(auth_args.debug, auth_args.quiet, other_args)
    except (
        Exception  # pylint: disable=broad-except
    ) as e:  # TODO Eventually we want to handle a certain set of exceptions, but this will do for now # pylint: disable=fixme
        print(f"There was an error querying the FERRY API: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
