import hashlib
import json
import pathlib
import sys
from typing import Any, Dict, Optional
import tempfile

import requests  # pylint: disable=import-error

try:
    from ferry_cli.helpers.auth import Auth
    from ferry_cli.helpers.debug_level import DebugLevel
    from ferry_cli.config.config import get_configfile_dir
except ImportError:
    from helpers.auth import Auth  # type: ignore
    from helpers.debug_level import DebugLevel  # type: ignore
    from config.config import get_configfile_dir  # type: ignore


# pylint: disable=unused-argument,pointless-statement,too-many-arguments
class FerryAPI:
    SWAGGER_JSON_ENDPOINT_DEFAULT = "swagger/swagger.json"
    SUPPORTED_METHODS = set(("get", "post", "put"))

    # pylint: disable=too-many-arguments
    def __init__(
        self: "FerryAPI",
        base_url: str,
        authorizer: Auth = Auth(),
        debug_level: DebugLevel = DebugLevel.NORMAL,
        dryrun: bool = False,
        swagger_endpoint: Optional[str] = None,
    ):
        """
        Parameters:
            base_url (str):  The root URL from which all FERRY API URLs are constructed
            authorizer (Callable[[requests.Session, requests.Session]): A function that prepares the requests session by adding any necessary auth data
            debug_level (DebugLevel): Level of debugging.  Can be DebugLevel.QUIET, DebugLevel.NORMAL, or DebugLevel.DEBUG
            dryrun (bool): Whether or not this is a test run.  If True, the intended URL will be printed, but the HTTP request will not be made
            swagger_endpoint (Optional[str]): The API endpoint (after base_url) to obtain the swagger.json file from the FERRY server.  If set to None, will use the default self.SWAGGER_JSON_ENDPOINT_DEFAULT.
        """
        self.base_url = base_url
        self.authorizer = authorizer
        self.debug_level = debug_level
        self.dryrun = dryrun
        self.swagger_endpoint = (
            swagger_endpoint if swagger_endpoint else self.SWAGGER_JSON_ENDPOINT_DEFAULT
        )
        self.swagger_file: pathlib.Path = self._set_swagger_file()

        if not self.swagger_file.exists():
            self.get_latest_swagger_file()

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

        if method.lower() not in self.SUPPORTED_METHODS:
            raise ValueError(f"Unsupported HTTP method {method.lower()}.")

        # Send our request
        response = session.request(
            method=method.upper(),
            url=f"{self.base_url}{endpoint}",
            headers=headers,
            params=params,
        )

        if debug:
            print(f"\nCalled Endpoint: {response.request.url}")
        if not response.ok:
            raise RuntimeError(
                f" *** API Failure: Status code {response.status_code} returned from endpoint /{endpoint}"
            )
        output = response.json()

        output["request_url"] = response.request.url
        return output

    def get_latest_swagger_file(self: "FerryAPI") -> None:
        """
        Gets the latest swagger file from FERRY and saves it in either:
        1. Directory returned by config.get_configfile_dir()
        2. Directory returned by tempfile.gettempdir()

        The filename is computed using the base_url and swagger_endpoint of the FerryAPI instance.
        """
        if self.dryrun:
            print("Dryrun: skipping swagger.json fetching")
            return

        response = self.call_endpoint(self.swagger_endpoint)
        if not response:
            print("Failed to fetch swagger.json file")
            sys.exit(1)

        self.swagger_file = self._set_swagger_file()

        try:
            self.swagger_file.parent.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            print(f"Could not create dir {self.swagger_file.parent}")
            raise e

        with open(self.swagger_file, "w") as file:
            file.write(json.dumps(response, indent=4))

        return

    def _set_swagger_file(self: "FerryAPI") -> pathlib.Path:
        """
        Returns a pathlib.Path where the swagger.json file should be saved.  In
        order of precedence, will return a pathlib.Path whose parent is:
        1. Directory returned by config.get_configfile_dir()
        2. Directory returned by tempfile.gettempdir()

        The filename within that directory is the value returned by FerryAPI._swagger_filename
        """
        _config_dir = get_configfile_dir()
        config_dir = (
            _config_dir
            if _config_dir is not None
            else pathlib.Path(tempfile.gettempdir())
        )

        self.swagger_file = config_dir / self._swagger_filename()
        return self.swagger_file

    def _swagger_filename(self: "FerryAPI") -> str:
        """
        Generate hash of endpoint including base_url
        """
        hasher = hashlib.sha256()
        hasher.update(f"{self.base_url}/{self.swagger_endpoint}".encode("utf-8"))
        suffix = hasher.hexdigest()[:16]
        return f"swagger_{suffix}.json"
