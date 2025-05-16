import json
import sys
from typing import Any, Dict

import requests  # pylint: disable=import-error

try:
    from ferry_cli.helpers.auth import Auth, DebugLevel
    from ferry_cli.config import CONFIG_DIR
except ImportError:
    from helpers.auth import Auth, DebugLevel  # type: ignore
    from config import CONFIG_DIR  # type: ignore


# pylint: disable=unused-argument,pointless-statement,too-many-arguments
class FerryAPI:
    # pylint: disable=too-many-arguments
    def __init__(
        self: "FerryAPI",
        base_url: str,
        authorizer: Auth = Auth(),
        debug_level: DebugLevel = DebugLevel.NORMAL,
        dryrun: bool = False,
    ):
        """
        Parameters:
            base_url (str):  The root URL from which all FERRY API URLs are constructed
            authorizer (Callable[[requests.Session, requests.Session]): A function that prepares the requests session by adding any necessary auth data
            debug_level (DebugLevel): Level of debugging.  Can be DebugLevel.QUIET, DebugLevel.NORMAL, or DebugLevel.DEBUG
            dryrun (bool): Whether or not this is a test run.  If True, the intended URL will be printed, but the HTTP request will not be made
        """
        self.base_url = base_url
        self.authorizer = authorizer
        self.debug_level = debug_level
        self.dryrun = dryrun

    # pylint: disable=dangerous-default-value,too-many-arguments
    def call_endpoint(
        self: "FerryAPI",
        endpoint: str,
        method: str = "get",
        data: Dict[Any, Any] = {},
        headers: Dict[str, Any] = {},
        params: Dict[Any, Any] = {},
        extra: Dict[Any, Any] = {},
    ) -> Any:
        # Create a session object to persist certain parameters across requests
        if self.dryrun:
            print(
                f"\nWould call endpoint: {self.base_url}{endpoint} with params\n{params}"
            )
            return None

        debug = self.debug_level == DebugLevel.DEBUG

        if debug:
            print(f"\nCalling Endpoint: {self.base_url}{endpoint}")

        _session = requests.Session()
        session = self.authorizer(_session)  # Handles auth for session

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
                    f"{self.base_url}{endpoint}", params=params, headers=headers
                )
            elif method.lower() == "put":
                response = session.put(
                    f"{self.base_url}{endpoint}", params=params, headers=headers
                )
            else:
                raise ValueError("Unsupported HTTP method.")
            if debug:
                print(f"Called Endpoint: {response.request.url}")
            output = response.json()

            output["request_url"] = response.request.url
            return output
        except BaseException as e:
            # How do we want to handle errors?
            raise e

    def get_latest_swagger_file(self: "FerryAPI") -> None:

        response = self.call_endpoint("docs/swagger.json")
        if response:
            with open(f"{CONFIG_DIR}/swagger.json", "w") as file:
                file.write(json.dumps(response, indent=4))
        else:
            print("Failed to fetch swagger.json file")
            sys.exit(1)
