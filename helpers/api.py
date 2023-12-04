import json
import os

import requests

class FerryAPI:
    def __init__(self, base_url, cert, capath, quiet = False):
        self.base_url = base_url
        self.cert = cert
        self.capath = capath
        self.quiet = quiet

    def call_endpoint(self, endpoint, method='get', data={}, headers={}, params={}, extra={}):
        # Create a session object to persist certain parameters across requests
        session = requests.Session()
        session.cert = self.cert
        session.verify = self.capath
        if extra:
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
            if not self.quiet:
                print(f"Called Endpoint: {response.request.url}")
            output = response.json()
            if output.get("ferry_status", None) != "success":
                exit(f"API Error: {output.get('ferry_error', 'Unknown Error')}")
            output["request_url"] = response.request.url
            return  output
        except BaseException as e:
            # How do we want to handle errors?
            raise e
    
            
        