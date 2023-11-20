import requests
import json
import os

class FerryAPI:
    def __init__(self, base_url, cert, capath, quiet = False):
        self.base_url = base_url
        self.cert = cert
        self.capath = capath
        self.quiet = quiet

    def generate_request(self, endpoint, method='get', data=None, headers=None, args=None, extra=None):
        # Create a session object to persist certain parameters across requests
        if not self.quiet:
            print(f"\nEndpoint: {endpoint}")
        session = requests.Session()
        session.cert = self.cert
        session.verify = self.capath
        if args:
            if type(args) != type(dict()):
                args = {attribute_name : attribute_value for attribute_name, attribute_value in vars(args).items() if attribute_value}
        params = args
        if extra:
            if type(extra) != type(dict()):
                extra =  {attribute_name : attribute_value for attribute_name, attribute_value in vars(extra).items() if attribute_value}
            for attribute_name, attribute_value in extra:
                if attribute_name not in params:
                    params[attribute_name] = attribute_value
        # I believe they are all actually "GET" calls
        try:
            if method.lower() == 'get':
                response = session.get(f"{self.base_url}{endpoint}", headers=headers, params=params)
            elif method.lower() == 'post':
                response = session.post(f"{self.base_url}{endpoint}", data=data, headers=headers)
            else:
                raise ValueError("Unsupported HTTP method.")
        except BaseException as e:
            # How do we want to handle errors?
            raise e
        
        with open("result.json","w") as file:
            formatted_json = json.dumps(response.json(), indent=4)
            file.write(formatted_json)
            if not self.quiet:
                self.print_steps(response.request.url, formatted_json)
            else:
                print(f"Response in file: {os.path.abspath(os.environ.get('PWD', ''))}/result.json")
                
        return (response.request.url, response.json())
    
    def print_steps(self, url, output):
        print(f"\nCalling: \"{url}\"")
        # Don't print excessively long responses - just store them in the result.json file and point to it.
        if len(output) < 1000:
            print(f"\nResponse: {output}")
        else:
            print(f"\nResponse in file: {os.path.abspath(os.environ.get('PWD', ''))}/result.json")
        