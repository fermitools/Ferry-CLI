import difflib
import json
import os

import requests

from helpers.updaters import SwaggerChanges

class FerryAPI:
    def __init__(self, base_url, cert, capath, quiet = False, is_workflow=False):
        self.base_url = base_url
        self.cert = cert
        self.capath = capath
        self.quiet = quiet
        self.is_workflow = is_workflow
        
    def get_latest_swagger_file(self):
        self.find_differences()
        return
        session = requests.Session()
        session.cert = self.cert
        session.verify = self.capath
        response = session.get(f"{self.base_url}docs/swagger.json")
        if response.status_code == 200:
            with open("/home/ltrestka/Ferry-CLI/tmp/swagger.json", "wb") as file:
                file.write(response.content)
                self.find_differences()
        else:
            print(f"Failed to retrieve the file: Status code {response.status_code}")

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
            return output
        except BaseException as e:
            # How do we want to handle errors?
            raise e
        
    def find_differences(self, outfile="tmp/differences.json"):
        # Load the JSON files
        with open('swagger.json', 'r') as file:
            json1 = json.load(file)
            old_version = json1["info"]["version"] if json1 else None
            old_endpoints = json1.get("paths", None) if json1 else None
        with open('tmp/swagger.json', 'r') as file:
            json2 = json.load(file)
            new_version = json2["info"]["version"] if json2 else None
            new_endpoints = json2.get("paths", None) if json2 else None
        
        path = "paths"
        changes = SwaggerChanges(old_version, new_version)
        changes.compare_json(path, old_endpoints, new_endpoints)
        
         # Compare the JSON objects and write differences to a file
        with open(outfile, 'w') as file_out:
            totals, differences = changes.get_totals()
            file_out.write(json.dumps(differences, indent=4))
            print(f"See {outfile} for a complete list of differences")
            exit(0)
        
