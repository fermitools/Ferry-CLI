from abc import ABC
from os import geteuid
import os.path
from typing import Optional

import requests
import requests.auth


__all__ = [
    "Auth",
    "DEFAULT_CA_DIR",
    "get_default_token_string",
    "get_default_cert_path",
    "AuthToken",
    "AuthCert",
]

DEFAULT_CA_DIR = "/etc/grid-security/certificates"


def get_default_token_string() -> str:
    """Follow the WLCG Bearer Token Discovery standard to get the token string.
    The standard is here:  https://zenodo.org/records/3937438"""
    bearer_token_str = os.environ.get("BEARER_TOKEN")
    if bearer_token_str is not None:
        return bearer_token_str
    bearer_token_file = os.environ.get("BEARER_TOKEN_FILE")
    if bearer_token_file is not None:
        return read_in_token(bearer_token_file)
    xdg_runtime_dir = os.environ.get("XDG_RUNTIME_DIR")
    if xdg_runtime_dir is not None:
        token_file = f"{xdg_runtime_dir}/{default_token_file_name()}"
        return read_in_token(token_file)
    return read_in_token(f"/tmp/{default_token_file_name()}")


def default_token_file_name() -> str:
    """Returns the filename (basename) of a bearer token, following the WLCG Bearer Token Discovery standard"""
    uid = os.geteuid()
    return f"bt_u{uid}"


# TODO Test this by passing in "blahblah\n" into a temp file, read it, make sure we get the right result
# Thanks to https://github.com/fermitools/jobsub_lite/blob/master/lib/tarfiles.py for this tidbit
def read_in_token(token_path: str) -> str:
    """Read the contents of a token file from a given token path"""
    with open(token_path, "r", encoding="UTF-8") as f:
        _token_string = f.read()
        return _token_string.strip()  # Drop \n at end of token_string


def get_default_cert_path() -> str:
    """Get the default path where cigetcert stores x509 certificates.  If $X509_USER_PROXY is set, use that first"""
    env_location = os.environ.get("X509_USER_PROXY")
    if env_location is not None:
        return env_location
    uid = str(geteuid())
    return f"/tmp/x509up_u{uid}"


class Auth(ABC):
    """This is the base class on which all Auth classes should build"""

    def __call__(self: "Auth", s: requests.Session) -> requests.Session:
        return s


class AuthToken(Auth):
    """This is a callable class that modifies a requests.Session object to add token
    auth"""

    def __init__(self: "AuthToken", token_path: Optional[str] = None) -> None:
        self.token_string = (
            get_default_token_string()
            if token_path is None
            else read_in_token(token_path)
        )

    def __call__(self: "AuthToken", s: requests.Session) -> requests.Session:
        """Modify the passed in session to add token auth"""
        s.headers["Authorization"] = f"Bearer {self.token_string}"
        return s


class AuthCert(Auth):
    """This is a callable class that modifies a requests.Session object to add X509 Certificate
    auth"""

    def __init__(
        self: "AuthCert",
        cert_path: str = get_default_cert_path(),
        ca_path: str = DEFAULT_CA_DIR,
    ) -> None:
        if not os.path.exists(cert_path):
            raise FileNotFoundError(
                f"Cert file {cert_path} does not exist.  Please check the given path and try again."
            )
        else:
            self.cert_path = cert_path
        if not os.path.exists(ca_path):
            raise FileNotFoundError(
                f"CA dir {ca_path} does not exist.  Please check the given path and try again."
            )
        else:
            self.ca_path = ca_path

    def __call__(self: "AuthCert", s: requests.Session) -> requests.Session:
        """Modify the passed in session to use certificate auth"""
        s.cert = self.cert_path
        s.verify = self.ca_path
        return s
