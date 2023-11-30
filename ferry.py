import argparse
import json
import os
import textwrap

from helpers.customs import TConfig
from helpers.api import FerryAPI
from safeguards.dcs import SafeguardsDCS
from workflows.dcs_workflows import *

WORKFLOW_FUNCTIONS = {
    "getGroupInfo": GetGroupInfo
}
with open("workflows/supported_workflows.json", 'r') as file:
    SUPPORTED_WORKFLOWS = json.load(file)


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
        
    class Workflow:
        """_summary_
        describer: pointer to the description parser
        workflow_name: The name of the workflow (string)
        ferry_api: FerryAPI object, used for generating and facilitating requests to actual ferry endpoints 
        """ 
        def __init__(self, parse_description, workflow_name):
            if workflow_name not in SUPPORTED_WORKFLOWS:
                raise NotImplementedError(f"'{workflow_name}' is not a supported workflow.")
            self.name = workflow_name
            self.description = SUPPORTED_WORKFLOWS[workflow_name]["description"]
            self.params = SUPPORTED_WORKFLOWS[workflow_name]["params"]
            self.parser = self.init_parser(parse_description)
            
        def init_parser(self, parse_description):
            endpoint_description = parse_description(self.name, self.description, "Workflow")
            endpoint_parser = argparse.ArgumentParser(description=endpoint_description)
            for param in self.params:
                req = ": required" if param["required"] else ""
                param_description = parse_description("", param["description"], f"{param['type']}{req}")
                endpoint_parser.add_argument(f"--{param['name']}", type=str, help=param_description, required=param['required'])
            return endpoint_parser
        
        def run(self, ferry_api, params = {}):
            return WORKFLOW_FUNCTIONS[self.name](ferry_api, params)
        
    def get_arg_parser(self):
        parser = argparse.ArgumentParser(description="CLI for Ferry API endpoints")
        parser.add_argument('--cert', required=(self.cert is None), default=self.cert, help="Path to cert")
        parser.add_argument('--capath', required=(self.capath is None), default=self.capath, help="Certificate authority path")
        parser.add_argument('-le', '--list_endpoints', action='store_true', help="List all available endpoints")
        parser.add_argument('-lw', '--list_workflows', action='store_true', help="List all available custom workflows")
        parser.add_argument('-ep', '--endpoint_params', help="List parameters for the selected endpoint")
        parser.add_argument('-e', '--endpoint', help="API endpoint and parameters")
        parser.add_argument('-w', '--workflow', help="Execute supported workflows")
        parser.add_argument('--get_swagger', action='store_true', help="Get the latest official swagger.json file")
        parser.add_argument('-q', '--quiet', action='store_true', default=False, help="Hide output")
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
        print("Listing parameters for endpoint: %s%s" % (self.base_url,endpoint))
        print()
        subparser = self.endpoints.get(endpoint, None)
        if not subparser:
            print()
            print("Error: '%s' is not a valid endpoint. Run 'ferry -l' for a full list of available endpoints." % endpoint)
            print()
        else:
            print(subparser.format_help())
            print()

    def list_supported_workflows(self):
        for json_workflow in SUPPORTED_WORKFLOWS.keys():
            workflow = self.Workflow(self.parse_description, json_workflow)
            print(workflow.parser.description)
            print()
    
        
        
    def execute_endpoint(self, endpoint, params):
        subparser = self.endpoints.get(endpoint, None)
        if not subparser:
            print()
            print("Error: '%s' is not a valid endpoint. Run 'ferry -l' for a full list of available endpoints." % endpoint)
            print()
        else:
            # Here we take the additional args that a user passes for an endpoint, and we generate a request to the endpoint with the parameters provided.
            # We do not bother with verifying passed arguments at this point since ferry will do it for us. 
            params, _ = subparser.parse_known_args(params)
            return self.ferry_api.call_endpoint(endpoint, params=params.__dict__)

    def generate_endpoints(self):
        endpoints = {}
        with open("swagger.json", "r") as json_file:
            api_data = json.load(json_file)
            for path, data in api_data["paths"].items():
                endpoint = path.replace("/","")
                if "get" in data:
                    method="get"
                elif "post" in data:
                    method = "post"
                elif "put" in data:
                    method = "put"
                description = data[method]["description"]
                endpoint_description = self.parse_description(endpoint, description, method.upper())
                endpoint_parser = argparse.ArgumentParser(description=endpoint_description)
                for param in data[method].get("parameters", []):
                    param_description = self.parse_description("", param["description"], "%s%s" % (param["type"], ": required" if param.get("required",False) else ""))
                    endpoint_parser.add_argument(f"--{param['name']}", type=str, help=param_description, required=param.get("required",False))
                endpoints[path.replace("/","")] = endpoint_parser
        return endpoints
        
    def parse_description(self, name, desc, method=None):
        description_lines = textwrap.wrap(desc, width=60)
        first_line = description_lines[0]
        rest_lines = description_lines[1:]
        endpoint_description = "%s" % (name.replace("/", ""))
        method_char_count = 49 - len("(%s)" % method)
        endpoint_description = f"{endpoint_description:<{method_char_count}} ({method}) | {first_line}\n"
        for line in rest_lines:
            endpoint_description += f"{'':<50} | {line}\n"
        return endpoint_description

    
    def run(self):
        
        args, endpoint_args = self.parser.parse_known_args()
        
        self.cert = args.cert
        self.capath = args.capath
        if args.get_swagger:
            self.ferry_api = FerryAPI(self.base_url, self.cert, self.capath, args.quiet)
            return self.ferry_api.get_latest_swagger_file()
        if args.endpoint:
            # Prevent DCS from running this endpoint if necessary, and print proper steps to take instead.
            self.safeguards.verify(args.endpoint)
            endpoint_parser = self.endpoints.get(args.endpoint, None)
            if endpoint_parser:
                self.ferry_api = FerryAPI(self.base_url, self.cert, self.capath, args.quiet)
                json_result = self.execute_endpoint(args.endpoint, endpoint_args)
                if not args.quiet:
                    self.handle_output(json_result)
            else:
                print(f"Error: '{self.base_url}{args.endpoint}' is not an existing Ferry endpoint.")
                exit(1)
        elif args.workflow:
            if args.workflow in SUPPORTED_WORKFLOWS:
                workflow = self.Workflow(self.parse_description, args.workflow)
            if workflow and workflow.parser:
                self.ferry_api = FerryAPI(self.base_url, self.cert, self.capath, args.quiet, is_workflow=True)
                params, _ = workflow.parser.parse_known_args(endpoint_args)
                json_result = workflow.run(self.ferry_api, params.__dict__)
                if not args.quiet:
                    self.handle_output(json_result)
            else:
                print(f"Error: '{self.base_url}{args.endpoint}' is not an existing Ferry endpoint.")
                exit(1)
        elif args.list_endpoints:
            self.list_available_endpoints()
        elif args.list_workflows:
            self.list_supported_workflows()
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
            print(f"Response: {output}")
        else:
            with open("result.json","w") as file:
                file.write(output)
            print(f"Response in file: {os.path.abspath(os.environ.get('PWD', ''))}/result.json")
            
def main():
    ferry_api = FerryCLI()
    ferry_api.run()
            
if __name__ == "__main__":
    main()




