import json
import os

from helpers.customs import TConfig, FerryParser
from helpers.api import FerryAPI
from safeguards.dcs import SafeguardsDCS

from helpers.supported_workflows import SUPPORTED_WORKFLOWS

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
        parser = FerryParser.create(description="CLI for Ferry API endpoints")
        parser.add_argument('--cert', required=(self.cert is None), default=self.cert, help="Path to cert")
        parser.add_argument('--capath', required=(self.capath is None), default=self.capath, help="Certificate authority path")
        parser.add_argument('-le', '--list_endpoints', action='store_true', help="List all available endpoints")
        parser.add_argument('-lw', '--list_workflows', action='store_true', help="List all supported custom workflows")
        parser.add_argument('-ep', '--endpoint_params', help="List parameters for the specified endpoint")
        parser.add_argument('-wp', '--workflow_params', help="List parameters for the supported workflow")
        parser.add_argument('-e', '--endpoint', help="API endpoint and parameters")
        parser.add_argument('-w', '--workflow', help="Execute supported workflows")
        parser.add_argument('-q', '--quiet', action='store_true', default=False, help="Hide output")
        return parser
    
    def list_available_endpoints(self):
        print("""
              Listing all available endpoints:
              """)
        for subparser in self.endpoints.values():
            print(subparser.description)
    
    def get_endpoint_params(self, endpoint):
        print("""
              Listing parameters for endpoint: %s%s" 
              """ % (self.base_url,endpoint))
        subparser = self.endpoints.get(endpoint, None)
        if not subparser:
            print("""
                  Error: '%s' is not a valid endpoint. Run 'ferry -l' for a full list of available endpoints.
                  """ % endpoint)
        else:
            print(f"""{subparser.format_help()}
                  """)
            
        
    def execute_endpoint(self, endpoint, params):
        subparser = self.endpoints.get(endpoint, None)
        if not subparser:
            print("""
                  Error: '%s' is not a valid endpoint. Run 'ferry -l' for a full list of available endpoints.
                  """% endpoint)
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
                    
                endpoint_parser = FerryParser.create_subparser(endpoint, method=method.upper(), description=data[method]["description"])
                endpoint_parser.set_arguments(data[method].get("parameters", [])) 
                endpoints[path.replace("/","")] = endpoint_parser
        return endpoints
        

    def run(self):
        
        args, endpoint_args = self.parser.parse_known_args()
        
        self.cert = args.cert
        self.capath = args.capath
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
                # Finds workflow inherited class in dictionary if exists, and initializes it.
                workflow = SUPPORTED_WORKFLOWS[args.workflow]()
                workflow.init_parser()
                self.ferry_api = FerryAPI(self.base_url, self.cert, self.capath, args.quiet, is_workflow=True)
                params, _ = workflow.parser.parse_known_args(endpoint_args)
                json_result = workflow.run(self.ferry_api, params.__dict__)
                if not args.quiet:
                    self.handle_output(json.dumps(json_result, indent=4))
            else:
                print(f"Error: '{args.workflow}' is not a supported workflow.")
                exit(1)
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
            if args.workflow_params in SUPPORTED_WORKFLOWS:
                # Finds workflow inherited class in dictionary if exists, and initializes it.
                workflow = SUPPORTED_WORKFLOWS[args.workflow_params]()
                workflow.init_parser()
                workflow.get_info()
            else:
                print(f"Error: '{args.workflow_params}' is not a supported workflow.")
                exit(1)
        else:
            self.parser.print_help()
            
    # TBD if we will use this at all
    def handle_output(self, output):
        # Don't print excessively long responses - just store them in the result.json file and point to it.
        if len(str(output)) < 1000:
            print(f"Response: {json.dumps(output, indent=4)}")
        else:
            with open("result.json","w") as file:
                file.write(json.dumps(output, indent=4))
            print(f"Response in file: {os.path.abspath(os.environ.get('PWD', ''))}/result.json")
            
def main():
    ferry_api = FerryCLI()
    ferry_api.run()
            
if __name__ == "__main__":
    main()




