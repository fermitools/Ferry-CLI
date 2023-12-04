import json
import os
import sys
import textwrap
from typing import Any, Dict, Optional, List, Tuple, Type

from helpers.customs import TConfig, FerryParser
from helpers.supported_workflows import SUPPORTED_WORKFLOWS
from helpers.api import FerryAPI
from helpers.auth import *
from safeguards.dcs import SafeguardsDCS


def get_default_paths(config: TConfig) -> Tuple[str, str]:
    cert = config.get_from("Auth", "default_cert_path", check_path=True)
    capath = config.get_from("Auth", "default_capath", check_path=True)
    return cert, capath


def set_auth_from_args(
    auth_method: str, token_path: str, cert_path: str, ca_path: str
) -> Auth:
    """Set the auth class based on the given arguments"""
    if auth_method == "token":
        print("Using token auth")
        return AuthToken(token_path)
    elif auth_method == "cert" or auth_method == "certificate":
        print("Using cert auth")
        return AuthCert(cert_path, ca_path)
    else:
        raise ValueError(
            "Unsupported auth method!  Please use one of the following auth methods: ['token', 'cert', 'certificate']"
        )


class FerryCLI:
    def __init__(self: "FerryCLI") -> None:
        self.config = TConfig()
        self.base_url = self.config.get_from("Ferry", "base_url")
        self.endpoints = self.generate_endpoints()
        self.safeguards = SafeguardsDCS()
        self.parser = self.get_arg_parser()
        
    def get_arg_parser(self: "FerryCLI") -> FerryParser:
        parser = FerryParser.create(description="CLI for Ferry API endpoints")
        parser.add_argument(
            "-a", "--auth-method", default="token", help="Auth method for FERRY request"
        )
        auth_group = parser.add_mutually_exclusive_group(required=False)
        auth_group.add_argument(
            "--token-path",
            default=get_default_token_path(),
            help="Path to bearer token",
        )
        auth_group.add_argument(
            "--cert-path", default=get_default_cert_path(), help="Path to cert"
        )
        parser.add_argument(
            "--ca-path", default=DEFAULT_CA_DIR, help="Certificate authority path"
        )
        parser.add_argument(
            "-le",
            "--list_endpoints",
            action="store_true",
            help="List all available endpoints",
        )
        parser.add_argument(
            '-lw', 
            '--list_workflows', 
            action='store_true', 
            help="List all supported custom workflows"
        )
        parser.add_argument(
            '-ep', 
            '--endpoint_params', 
            help="List parameters for the selected endpoint"
        )
        parser.add_argument(
            '-wp', 
            '--workflow_params', 
            help="List parameters for the supported workflow"
        )
        parser.add_argument(
            '-e', '--endpoint', help="API endpoint and parameters"
        )
        parser.add_argument(
            '-w', '--workflow', help="Execute supported workflows"
            )
        parser.add_argument(
            '-q', '--quiet', action='store_true', default=False, help="Hide output"
        )
        return parser
    
    def list_available_endpoints(self: "FerryCLI") -> None:
        print("""
              Listing all available endpoints:
              """)
        for subparser in self.endpoints.values():
            print(subparser.description)
    
    def get_endpoint_params(self: "FerryCLI", endpoint: str) -> None:
        print("""
              Listing parameters for endpoint: %s%s" 
              """ % (self.base_url,endpoint))
        subparser = self.endpoints.get(endpoint, None)
        if not subparser:
            print("""
                  Error: '%s' is not a valid endpoint. Run 'ferry -l' for a full list of available endpoints.
                  """ % endpoint)
        else:
            print(subparser.format_help())
            print()

    def execute_endpoint(self: "FerryCLI", endpoint: str, params: List[str]) -> str:
        try:
            subparser = self.endpoints[endpoint]
        except KeyError:
            raise ValueError(
                f"Error: '{endpoint}' is not a valid endpoint. Run 'ferry -l' for a full list of available endpoints."
            )
        else:
            params_args, _ = subparser.parse_known_args(params)
            return self.ferry_api.call_endpoint(endpoint, params=vars(params_args))

    def generate_endpoints(self: "FerryCLI") -> Dict[str, FerryParser]:
        endpoints = {}
        with open("swagger.json", "r") as json_file:
            api_data = json.load(json_file)
            for path, data in api_data["paths"].items():
                endpoint = path.replace("/", "")
                if "get" in data:
                    method = "get"
                elif "post" in data:
                    method = "post"
                elif "put" in data:
                    method = "put"
                    
                endpoint_parser = FerryParser.create_subparser(endpoint, method=method.upper(), description=data[method]["description"])
                endpoint_parser.set_arguments(data[method].get("parameters", [])) 
                endpoints[path.replace("/","")] = endpoint_parser
        return endpoints

    def parse_description(
        self: "FerryCLI", name: str, desc: str, method: Optional[str] = None
    ) -> str:
        description_lines = textwrap.wrap(desc, width=60)
        first_line = description_lines[0]
        rest_lines = description_lines[1:]
        endpoint_description = "%s" % (name.replace("/", ""))
        method_char_count = 49 - len("(%s)" % method)
        endpoint_description = (
            f"{endpoint_description:<{method_char_count}} ({method}) | {first_line}\n"
        )
        for line in rest_lines:
            endpoint_description += f"{'':<50} | {line}\n"
        return endpoint_description

    def run(self: "FerryCLI") -> None:
        args, endpoint_args = self.parser.parse_known_args()
        authorizer = set_auth_from_args(
            args.auth_method, args.token_path, args.cert_path, args.ca_path
        )
        if args.endpoint:
            # Prevent DCS from running this endpoint if necessary, and print proper steps to take instead.
            self.safeguards.verify(args.endpoint)
            try:
                self.ferry_api = FerryAPI(
                    base_url=self.base_url, authorizer=authorizer, quiet=args.quiet
                )
                json_result = self.execute_endpoint(args.endpoint, endpoint_args)
            except Exception as e:
                raise Exception(f"{e}")
            if not args.quiet:
                self.handle_output(json.dumps(json_result, indent=4))
        elif args.workflow:
            try:
                # Finds workflow inherited class in dictionary if exists, and initializes it.
                workflow = SUPPORTED_WORKFLOWS[args.workflow]()
                workflow.init_parser()
                self.ferry_api = FerryAPI(
                        base_url=self.base_url, authorizer=authorizer, quiet=args.quiet
                    )
                workflow_params, _ = workflow.parser.parse_known_args(endpoint_args)
                json_result = workflow.run(self.ferry_api, vars(workflow_params))
                if not args.quiet:
                    self.handle_output(json.dumps(json_result, indent=4))
            except Exception as e:
                    raise Exception(f"Error: '{args.workflow}' is not a supported workflow.")
        elif args.list_endpoints:
            self.list_available_endpoints()
        elif args.list_workflows:
            print("\nListing all supported workflows: \n")
            for workflow in SUPPORTED_WORKFLOWS.values():
                workflow().get_description()
        elif args.endpoint_params:
            # Prevent DCS from running this endpoint if necessary, and print proper steps to take instead.
            self.safeguards.verify(args.endpoint_params)
            self.get_endpoint_params(args.endpoint_params)
        elif args.workflow_params:
            try:
                # Finds workflow inherited class in dictionary if exists, and initializes it.
                workflow = SUPPORTED_WORKFLOWS[args.workflow_params]()
                workflow.init_parser()
                workflow.get_info()
            except KeyError as e:
                raise KeyError(f"Error: '{args.workflow_params}' is not a supported workflow.")
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
    ferry_api = FerryCLI()
    try:
        ferry_api.run()
    except (
        Exception
    ) as e:  # TODO Eventually we want to handle a certain set of exceptions, but this will do for now
        print(f"There was an error querying the FERRY API: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
