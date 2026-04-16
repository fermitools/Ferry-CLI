from abc import ABC
from argparse import Namespace
import enum
from os import geteuid
import os.path
from typing import List, Optional, Tuple

# pylint: disable=import-error,no-else-return
import requests
import requests.auth

try:
    from ferry_cli.helpers.customs import FerryParser
    from ferry_cli.version import request_project_info
except ImportError:
    from helpers.customs import FerryParser  # type: ignore
    from version import request_project_info  # type: ignore


__all__ = [
    "Auth",
    "DEFAULT_CA_DIR",
    "get_default_token_string",
    "get_default_cert_path",
    "AuthToken",
    "AuthCert",
]

DEFAULT_CA_DIR = "/etc/grid-security/certificates"


def get_default_token_string(debug: bool = False) -> str:
    """Follow the WLCG Bearer Token Discovery standard to get the token string.
    The standard is here:  https://zenodo.org/records/3937438"""
    bearer_token_str = os.environ.get("BEARER_TOKEN")
    if bearer_token_str is not None:
        if debug:
            print("BEARER_TOKEN is set:  using string value of BEARER_TOKEN")
        return bearer_token_str
    bearer_token_file = os.environ.get("BEARER_TOKEN_FILE")
    if bearer_token_file is not None:
        if debug:
            print(
                f"BEARER_TOKEN_FILE is set:  using file contents of {bearer_token_file}"
            )
        return read_in_token(bearer_token_file)
    filename = default_token_file_name()
    xdg_runtime_dir = os.environ.get("XDG_RUNTIME_DIR")
    if xdg_runtime_dir is not None:
        token_file = f"{xdg_runtime_dir}/{filename}"
        if debug:
            print(f"XDG_RUNTIME_DIR is set:  using file contents of {token_file}")
        return read_in_token(token_file)
    fallback_token_file = f"/tmp/{filename}"
    if debug:
        print(f"Fallback: using file contents of /tmp/{filename}")
    return read_in_token(fallback_token_file)


def default_token_file_name() -> str:
    """Returns the filename (basename) of a bearer token, following the WLCG Bearer Token Discovery standard"""
    uid = os.geteuid()
    return f"bt_u{uid}"


# Thanks to https://github.com/fermitools/jobsub_lite/blob/master/lib/tarfiles.py for this tidbit
def read_in_token(token_path: str) -> str:
    """Read the contents of a token file from a given token path"""
    with open(token_path, "r", encoding="UTF-8") as f:
        _token_string = f.read()
        return _token_string.strip()  # Drop \n at end of token_string


def get_default_cert_path(debug: bool = False) -> str:
    """Get the default path where cigetcert stores x509 certificates.  If $X509_USER_PROXY is set, use that first"""
    env_location = os.environ.get("X509_USER_PROXY")
    if env_location is not None:
        if debug:
            print(
                f"X509_USER_PROXY is set.  Using proxy from X509_USER_PROXY location: {env_location}"
            )
        return env_location
    uid = str(geteuid())
    fallback_location = f"/tmp/x509up_u{uid}"
    if debug:
        print(f"Using fallback location: {fallback_location}")
    return fallback_location


class Auth(ABC):
    """This is the base class on which all Auth classes should build"""

    def __call__(self: "Auth", s: requests.Session) -> requests.Session:
        raise NotImplementedError(
            "Must use a subclass of Auth with __call__ method defined"
        )


class AuthToken(Auth):
    """This is a callable class that modifies a requests.Session object to add token
    auth"""

    def __init__(
        self: "AuthToken", token_path: Optional[str] = None, debug: bool = False
    ) -> None:
        self.debug = debug
        try:
            self.token_string = (
                get_default_token_string(debug)
                if token_path is None
                else read_in_token(token_path)
            )
        except FileNotFoundError:
            raise FileNotFoundError(  # pylint: disable=raise-missing-from
                f"Bearer token file not found. Please verify that you have a valid token in the specified, or default path: /tmp/{default_token_file_name()}, or run 'htgettoken -a htvaultprod.fnal.gov -i fermilab'"
            )

    def __call__(self: "AuthToken", s: requests.Session) -> requests.Session:
        """Modify the passed in session to add token auth"""
        s.headers["Authorization"] = f"Bearer {self.token_string}"
        if self.debug:
            print('\nAdding Authorization header: "Bearer XXXXXXXXXXX" to HTTP session')
            print("Actual Token string redacted\n")
        return s


class AuthCert(Auth):
    """This is a callable class that modifies a requests.Session object to add X509 Certificate
    auth"""

    def __init__(
        self: "AuthCert",
        cert_path: Optional[str] = None,
        ca_path: str = DEFAULT_CA_DIR,
        debug: bool = False,
    ) -> None:
        self.debug = debug
        self.cert_path = (
            get_default_cert_path(self.debug) if cert_path is None else cert_path
        )
        if not os.path.exists(self.cert_path):
            raise FileNotFoundError(
                f"Cert file {cert_path} does not exist. Please check the given path and try again. Make sure you have Kerberos ticket, then run kx509"
            )
        if not os.path.exists(ca_path):
            raise FileNotFoundError(
                f"CA dir {ca_path} does not exist. Please check the given path and try again."
            )
        self.ca_path = ca_path

    def __call__(self: "AuthCert", s: requests.Session) -> requests.Session:
        """Modify the passed in session to use certificate auth"""
        s.cert = self.cert_path
        s.verify = self.ca_path
        if self.debug:
            print(
                f"\nSetting Session cert attribute to {self.cert_path} and verify attribute to {self.ca_path}"
            )
        return s


def get_auth_parser() -> "FerryParser":
    auth_parser = FerryParser.create(
        description="CLI for Ferry API endpoints", add_help=False
    )
    auth_parser.add_argument(
        "-a", "--auth-method", default="token", help="Auth method for FERRY request"
    )
    auth_group = auth_parser.add_mutually_exclusive_group(required=False)
    auth_group.add_argument(
        "--token-path",
        help="Path to bearer token",
    )
    auth_group.add_argument("--cert-path", help="Path to cert")
    auth_parser.add_argument(
        "--ca-path", default=DEFAULT_CA_DIR, help="Certificate authority path"
    )
    output_group = auth_parser.add_mutually_exclusive_group(required=False)
    output_group.add_argument(
        "--dryrun",
        action="store_true",
        default=False,
        help="Populate the API call(s) but don't actually run them",
    )
    output_group.add_argument(
        "-d",
        "--debug",
        action="store_const",
        dest="debug_level",
        const=DebugLevel.DEBUG,
        default=DebugLevel.NORMAL,
        help="Turn on debugging",
    )
    output_group.add_argument(
        "-q",
        "--quiet",
        action="store_const",
        dest="debug_level",
        const=DebugLevel.QUIET,
        default=DebugLevel.NORMAL,
        help="Hide output",
    )
    auth_parser.add_argument(
        "-u",
        "--update",
        action="store_true",
        default=False,
        help="Get latest swagger file",
    )
    auth_parser.add_argument(
        "--support_email",
        nargs=0,
        help="Get Ferry CLI support emails",
        action=request_project_info("email"),
    )
    auth_parser.add_argument(
        "-s",
        "--server",
        help="Server URL to use instead of configuration file api.base_url value",
    )
    auth_parser.add_argument(
        "--version",
        nargs=0,
        help="Get Ferry CLI version",
        action=request_project_info("version"),
    )
    return auth_parser


def set_auth_from_args(args: Namespace) -> Auth:
    """Set the auth class based on the given arguments"""
    debug = args.debug_level == DebugLevel.DEBUG
    if args.auth_method == "token":
        if debug:
            print("\nUsing token auth")
        return AuthToken(args.token_path, debug)
    elif args.auth_method in ["cert", "certificate"]:
        if debug:
            print("\nUsing cert auth")
        return AuthCert(args.cert_path, args.ca_path, debug)
    else:
        raise ValueError(
            "Unsupported auth method!  Please use one of the following auth methods: ['token', 'cert', 'certificate']"
        )


def get_auth_args() -> Tuple[Namespace, List[str]]:
    parser = get_auth_parser()
    auth_args, other_args = parser.parse_known_args()
    return auth_args, other_args


class DebugLevel(enum.Enum):
    QUIET = 0
    NORMAL = 1
    DEBUG = 2
