import json
import os
from typing import Dict, Type

import requests

from .auth import AuthToken, AuthCert


SUPPORTED_AUTH_METHODS: Dict[str, Type[object]] = {
    "token": AuthToken, 
    "cert": AuthCert,
    "certificate": AuthCert
}


class FerryAPI:
    def __init__(self, base_url, auth_method='token', auth_kwargs: Dict[str, str] = {} , quiet = False):
        self.base_url = base_url
        self.authorizer = self._map_auth_method_to_authorizer(auth_method) 
        self.auth_kwargs = auth_kwargs
        self.quiet = quiet

    def call_endpoint(
        self, endpoint, method="get", data={}, headers={}, params={}, extra={}
    ):
        # Create a session object to persist certain parameters across requests
        if not self.quiet:
            print(f"\nCalling Endpoint: {self.base_url}{endpoint}")

        _session = requests.Session()
        session = self.authorizer(_session, **self.auth_kwargs) # Handles auth for session

        if extra:
            for attribute_name, attribute_value in extra:
                if attribute_name not in params:
                    params[attribute_name] = attribute_value
        # I believe they are all actually "GET" calls
        try:
            if method.lower() == "get":
                response = session.get(
                    f"{self.base_url}{endpoint}", headers=headers, params=params
                )
            elif method.lower() == "post":
                response = session.post(
                    f"{self.base_url}{endpoint}", data=data, headers=headers
                )
            else:
                raise ValueError("Unsupported HTTP method.")
            output = response.json()
            output["request_url"] = response.request.url
            return json.dumps(output, indent=4)
        except BaseException as e:
            # How do we want to handle errors?
            raise e

    def _map_auth_method_to_authorizer(self: 'FerryAPI', auth_method: str = 'token') -> Type[object]:
        try:
            authorizer = SUPPORTED_AUTH_METHODS[auth_method]()
            return authorizer
        except KeyError:
            raise ValueError(f"Unsupported auth method given {auth_method}.  Supported auth methods are {list(SUPPORTED_AUTH_METHODS.keys())}")
            


            
        
