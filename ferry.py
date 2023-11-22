import argparse
import json
import os
import textwrap

from helpers.customs import TConfig
from helpers.api import FerryAPI
from safeguards.dcs import SafeguardsDCS


def get_default_paths(config):
    cert = config.get_from("Auth", "default_cert_path", check_path=True)
    capath = config.get_from("Auth", "default_capath", check_path=True)
    return cert, capath


class FerryCLI:
    def __init__(self):
        self.config = TConfig()
        self.base_url = self.config.get_from("Ferry", "base_url")
        self.endpoints = self.generate_endpoints()
        self.safeguards = SafeguardsDCS()
        self.cert, self.capath = get_default_paths(self.config)
        self.parser = self.get_arg_parser()

    def get_arg_parser(self):
        parser = argparse.ArgumentParser(description="CLI for Ferry API endpoints")
        parser.add_argument(
            "--cert",
            required=(self.cert is None),
            default=self.cert,
            help="Path to cert",
        )
        parser.add_argument(
            "--capath",
            required=(self.capath is None),
            default=self.capath,
            help="Certificate authority path",
        )
        parser.add_argument(
            "-l",
            "--list_endpoints",
            action="store_true",
            help="List all available endpoints",
        )
        parser.add_argument(
            "-ep", "--endpoint_params", help="List parameters for the selected endpoint"
        )
        parser.add_argument("-e", "--endpoint", help="API endpoint and parameters")
        parser.add_argument(
            "-q", "--quiet", action="store_true", default=False, help="Hide output"
        )
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

        self.cert = args.cert
        self.capath = args.capath
        if args.endpoint:
            # Prevent DCS from running this endpoint if necessary, and print proper steps to take instead.
            self.safeguards.verify(args.endpoint)
            endpoint_parser = self.endpoints.get(args.endpoint, None)
            if endpoint_parser:
                self.ferry_api = FerryAPI(
                    self.base_url, self.cert, self.capath, args.quiet
                )
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
    ferry_api.run()


if __name__ == "__main__":
    main()
