import argparse
import json
import os
import textwrap
import subprocess
from safeguards import safeguards

def get_default_cert_path():
        default_cert_path = f"/tmp/x509up_u{os.geteuid()}"
        if os.path.exists(default_cert_path):
            return default_cert_path
        else:
            return None
        
def get_default_capath():
    default_capath = "/etc/grid-security/certificates"
    if os.path.exists(default_capath):
        return default_capath
    else:
        return None
        
class FerryApi:
    def __init__(self):
        self.base_url = "https://ferry.fnal.gov:8445/"
        self.endpoints = {}
        self.generate_endpoints()
        self.cert = None
        self.capath = None
        self.parser = self.get_base_parser()
        
    def get_base_parser(self):
        self.cert = get_default_cert_path()
        self.capath = get_default_capath()
        parser = argparse.ArgumentParser(description="CLI for Ferry API endpoints")
        parser.add_argument('--cert', required=(self.cert is None), default=self.cert, help="Path to cert")
        parser.add_argument('--capath', required=(self.capath is None), default=self.capath, help="Certificate authority path")
        parser.add_argument('-l', '--list_endpoints', action='store_true', help="List all available endpoints")
        parser.add_argument('-ep', '--endpoint_params', help="List parameters for the selected endpoint")
        parser.add_argument('-e', '--endpoint', help="API endpoint and parameters")
        return parser
        
        
    def generate_url(self, endpoint, args, extra = None):
        print_args = ",\n   ".join([f"{attribute_name}={attribute_value}" for attribute_name, attribute_value in vars(args).items() if attribute_value])
        if print_args.replace("\n",""):
            print(f"\nArguments: [\n   {print_args}\n]")
            args_string = "?%s" % "&".join([f"{attribute_name}={attribute_value}" for attribute_name, attribute_value in vars(args).items() if attribute_value])
        else:
            args_string = ""
        if extra:
            param_join = "&" if "?" in args_string else "?"
            args_string = f"{args_string}{param_join}{extra}"
        return f"{self.base_url}{endpoint}{args_string}"

    def generate_command(self, url):
        command = [
            "curl",
            "-s",
            "--cert", self.cert,
            "--capath", self.capath,
            "%s" % url
        ]
        return command
    
        
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

                
    def execute_endpoint(self, endpoint, params):
        subparser = self.endpoints.get(endpoint, None)
        if not subparser:
            print()
            print("Error: '%s' is not a valid endpoint. Run 'ferry -l' for a full list of available endpoints." % endpoint)
            print()
            
        else:
            args, _ = subparser.parse_known_args(params)
            print(f"\nEndpoint: {endpoint}")
            extra = self.get_extras(endpoint, args)
            url = self.generate_url(endpoint, args, extra)
            command = self.generate_command(url)
            print(f"\nCalling: \"{' '.join(command).replace(' -s','')}\"")
            try:
                curl_output_bytes = subprocess.check_output(command)
                curl_output = curl_output_bytes.decode("utf-8")
                formatted_json = json.dumps(json.loads(curl_output), indent=4)
                
                # Don't print excessively long responses - just store them in the result.json file and point to it.
                if len(formatted_json) < 1000:
                    print(f"\nResponse: {formatted_json}\n\n")
                else:
                    print(f"\nResponse in file: {os.path.abspath(os.environ.get('PWD', ''))}/result.json\n\n")
                with open("result.json","w") as file:
                    file.write(formatted_json)
                return curl_output
            
            except subprocess.CalledProcessError as e:
                print("Error:", e)
            
    # This is where we will run other things to get information prior to our call, ie: if we need
    def get_extras(self, endpoint, args):
        extra=None
        if endpoint == "createGroup" and "groupname" in vars(args).keys() and "gid" not in vars(args).keys():
            extra = "gid=%s" % self.get_lowest_applicable_gid(vars(args).get("groupname", ""))
        
            
    def get_all_groups(self):
        command = self.generate_command("https://ferry.fnal.gov:8445/getAllGroups")
        curl_output_bytes = subprocess.check_output(command)
        curl_output = curl_output_bytes.decode("utf-8")
        return json.loads(curl_output)
    
    def get_group_info(self, group):
        group_json = self.get_all_groups()
        group_info = [entry for entry in group_json["ferry_output"] if entry["groupname"] == group]
        print(group_info)
        if group_info:
            print(group_info)
        
                
    def get_lowest_applicable_gid(self, experiment):
        group_json = self.get_all_groups()
        all_gids = [entry["gid"] for entry in group_json["ferry_output"]]
        exp_gids = [entry["gid"] for entry in group_json["ferry_output"] if entry["grouptype"] == "UnixGroup" and experiment in entry["groupname"]]
        if exp_gids:
            highest_gid = max(exp_gids)
        else:
            highest_gid = 0
        while highest_gid in all_gids:
            highest_gid = highest_gid + 1
        return highest_gid

    def generate_endpoints(self):
        with open("/home/ltrestka/ferry/swagger.json", "r") as json_file:
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
                self.endpoints[path.replace("/","")] = endpoint_parser

        
    def parse_description(self,name, desc, method=None):
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
        if args.endpoint:
            # Prevent DCS from running this endpoint if necessary, and print proper steps to take instead.
            safeguards().verify(args.endpoint)
            endpoint_parser = self.endpoints.get(args.endpoint, None)
            if endpoint_parser:
                return self.execute_endpoint(args.endpoint, endpoint_args)
        elif args.list_endpoints:
            self.list_available_endpoints()
        elif args.endpoint_params:
            # Prevent DCS from running this endpoint if necessary, and print proper steps to take instead.
            safeguards().verify(args.endpoint_params)
            self.get_endpoint_params(args.endpoint_params)
        else:
            self.parser.print_help()
            
def main():
    ferry_api = FerryApi()
    ferry_api.run()
            
if __name__ == "__main__":
    main()




