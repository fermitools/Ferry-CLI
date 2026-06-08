import json
import pathlib
import sys
import tempfile
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
    SWAGGER_JSON_ENDPOINT_DEFAULT = "docs/swagger.json"
    # pylint: disable=too-many-arguments
    def __init__(
        self: "FerryAPI",
        base_url: str,
        authorizer: Auth = Auth(),
        debug_level: DebugLevel = DebugLevel.NORMAL,
        dryrun: bool = False,
        swagger_endpoint: str | None = None,
    ):
        """
        Parameters:
            base_url (str):  The root URL from which all FERRY API URLs are constructed
            authorizer (Callable[[requests.Session, requests.Session]): A function that prepares the requests session by adding any necessary auth data
            debug_level (DebugLevel): Level of debugging.  Can be DebugLevel.QUIET, DebugLevel.NORMAL, or DebugLevel.DEBUG
            dryrun (bool): Whether or not this is a test run.  If True, the intended URL will be printed, but the HTTP request will not be made
            swagger_endpoint: str | None: The API endpoint (after base_url) to obtain the swagger.json file from the FERRY server.  If set to None, will use the default self.SWAGGER_JSON_ENDPOINT_DEFAULT.
        """
        self.base_url = base_url
        self.authorizer = authorizer
        self.debug_level = debug_level
        self.dryrun = dryrun
        self.swagger_endpoint = (
            swagger_endpoint if swagger_endpoint else self.SWAGGER_JSON_ENDPOINT_DEFAULT
        )

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
                print(f"\nCalled Endpoint: {response.request.url}")
            if not response.ok:
                raise RuntimeError(
                    f" *** API Failure: Status code {response.status_code} returned from endpoint /{endpoint}"
                )
            output = response.json()

            output["request_url"] = response.request.url
            return output
        except BaseException as e:
            # How do we want to handle errors?
            raise e

    # TODO: integration test
    def get_latest_swagger_file(self: "FerryAPI"):
        """
        Gets the latest swagger file from FERRY and set it in the class instance.
        Will save it in either:
        1. The directory returned by config.get_configfile_dir(), or
        2. tempfile.gettempdir(), if (1) doesn't return a valid directory
        """
        response = self.call_endpoint(self.swagger_endpoint)
        if not response and not self.dryrun:
            print("Failed to fetch swagger.json file")
            sys.exit(1)

        swagger_file = pathlib.Path(CONFIG_DIR) / "swagger.json"

        try:
            swagger_file.parent.mkdir(parents=True, exist_ok=True)
        except BaseException as e:
            print(f"Could not create dir {swagger_file.parent}")
            raise e

        with open(swagger_file, "w") as file:
            file.write(json.dumps(response, indent=4))

        if self.debug_level != DebugLevel.QUIET:
            print("Successfully stored latest swagger file.\n")
