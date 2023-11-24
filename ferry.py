import argparse
import json
import os
import sys
import textwrap
from typing import Type

from helpers.customs import TConfig
from helpers.api import FerryAPI
from helpers.auth import *
from safeguards.dcs import SafeguardsDCS


def get_default_paths(config):
    cert = config.get_from("Auth", "default_cert_path", check_path=True)
    capath = config.get_from("Auth", "default_capath", check_path=True)
    return cert, capath

def set_auth_from_args(auth_method, token_path, cert_path, ca_path: str) -> Type[object]:
    """Set the auth class based on the given arguments"""
    if auth_method == 'token':
        print("Using token auth")
        return AuthToken(token_path)
    elif auth_method == 'cert' or auth_method == 'certificate':
        print("Using cert auth")
        return AuthCert(cert_path, ca_path)
    else:
        raise ValueError("Unsupported auth method!  Please use one of the following auth methods: ['token', 'cert', 'certificate']")


class FerryCLI:
    def __init__(self):
        self.config = TConfig()
        self.base_url = self.config.get_from("Ferry", "base_url")
        self.endpoints = self.generate_endpoints()
        self.safeguards = SafeguardsDCS()
        self.parser = self.get_arg_parser()

    def get_arg_parser(self):
        parser = argparse.ArgumentParser(description="CLI for Ferry API endpoints")
        parser.add_argument("-a", "--auth-method", default='token', help="Auth method for FERRY request")
        parser.add_argument('--ca-path', default=DEFAULT_CA_DIR, help="Certificate authority path")
        parser.add_argument('-l', '--list_endpoints', action='store_true', help="List all available endpoints")
        parser.add_argument('-ep', '--endpoint_params', help="List parameters for the selected endpoint")
        parser.add_argument('-e', '--endpoint', help="API endpoint and parameters")
        parser.add_argument('-q', '--quiet', action='store_true', default=False, help="Hide output")

        auth_group = parser.add_mutually_exclusive_group(required=False)
        auth_group.add_argument("--cert-path", default=get_default_cert_path(), help="Path to cert")
        auth_group.add_argument("--token-path", default=get_default_token_path(), help="Path to bearer token")

        return parser

    def list_available_endpoints(self):
        print()
        print("Listing all available endpoints:")
        print()
        for subparser in self.endpoints.values():
            print(subparser.description)
            print()

    def get_endpoint_params(self, endpoint):
        print()
        print("Listing parameters for endpoint: %s%s" % (self.base_url, endpoint))
        print()
        subparser = self.endpoints.get(endpoint, None)
        if not subparser:
            print()
            print(
                "Error: '%s' is not a valid endpoint. Run 'ferry -l' for a full list of available endpoints."
                % endpoint
            )
            print()
        else:
            print(subparser.format_help())
            print()

    def execute_endpoint(self, endpoint, params):
        subparser = self.endpoints.get(endpoint, None)
        if not subparser:
            print()
            print(
                "Error: '%s' is not a valid endpoint. Run 'ferry -l' for a full list of available endpoints."
                % endpoint
            )
            print()
        else:
            params, _ = subparser.parse_known_args(params)
            return self.ferry_api.call_endpoint(endpoint, params=params.__dict__)

    def generate_endpoints(self):
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
                description = data[method]["description"]
                endpoint_description = self.parse_description(
                    endpoint, description, method.upper()
                )
                endpoint_parser = argparse.ArgumentParser(
                    description=endpoint_description
                )
                for param in data[method].get("parameters", []):
                    param_description = self.parse_description(
                        "",
                        param["description"],
                        "%s%s"
                        % (
                            param["type"],
                            ": required" if param.get("required", False) else "",
                        ),
                    )
                    endpoint_parser.add_argument(
                        f"--{param['name']}",
                        type=str,
                        help=param_description,
                        required=param.get("required", False),
                    )
                endpoints[path.replace("/", "")] = endpoint_parser
        return endpoints

    def parse_description(self, name, desc, method=None):
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

    def run(self):
        args, endpoint_args = self.parser.parse_known_args()

        if args.endpoint:
            authorizer = set_auth_from_args(args.auth_method, args.token_path, args.cert_path, args.ca_path)

            # Prevent DCS from running this endpoint if necessary, and print proper steps to take instead.
            self.safeguards.verify(args.endpoint)
            endpoint_parser = self.endpoints.get(args.endpoint, None)
            if endpoint_parser:
                try:
                    self.ferry_api = FerryAPI(base_url=self.base_url, authorizer=authorizer, quiet=args.quiet)
                except Exception as e:
                    print(f"Exception initializing FerryAPI: {e}")
                    raise
                json_result = self.execute_endpoint(args.endpoint, endpoint_args)
                if not args.quiet:
                    self.handle_output(json_result)
        elif args.list_endpoints:
            self.list_available_endpoints()
        elif args.endpoint_params:
            # Prevent DCS from running this endpoint if necessary, and print proper steps to take instead.
            self.safeguards.verify(args.endpoint_params)
            self.get_endpoint_params(args.endpoint_params)
        else:
            self.parser.print_help()

    # TBD if we will use this at all
    def handle_output(self, output):
        # Don't print excessively long responses - just store them in the result.json file and point to it.
        if len(output) < 1000:
            print(f"\nResponse: {output}")
        else:
            with open("result.json", "w") as file:
                file.write(output)
            print(
                f"\nResponse in file: {os.path.abspath(os.environ.get('PWD', ''))}/result.json"
            )


def main():
    ferry_api = FerryCLI()
    try:
        ferry_api.run()
    except Exception as e:  # TODO Eventually we want to handle a certain set of exceptions, but this will do for now
        print(f"There was an error querying the FERRY API: {e}")
        sys.exit(1)
            
if __name__ == "__main__":
    main()
