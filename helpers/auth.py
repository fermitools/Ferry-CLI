from os import geteuid
import os.path
import sys

import requests
import requests.auth


__all__ = [
    "DEFAULT_CA_DIR",
    "get_default_token_path",
    "get_default_cert_path",
    "AuthToken",
    "AuthCert",
]

DEFAULT_CA_DIR = "/etc/grid-security/certificates"


def get_default_token_path() -> str:
    """Get the default path where htgettoken stores bearer tokens.  If $BEARER_TOKEN_FILE is set, use that first"""
    env_location = os.environ.get("BEARER_TOKEN_FILE")
    if env_location is not None:
        return env_location
    uid = str(geteuid())
    return f"/run/user/{uid}/bt_u{uid}"


def get_default_cert_path() -> str:
    """Get the default path where cigetcert stores x509 certificates.  If $X509_USER_PROXY is set, use that first"""
    env_location = os.environ.get("X509_USER_PROXY")
    if env_location is not None:
        return env_location
    uid = str(geteuid())
    return f"/tmp/x509up_u{uid}"


class AuthToken(object):
    """This is a callable class that modifies a requests.Session object to add token
    auth"""

    def __init__(self: "AuthToken", token_path: str = get_default_token_path()) -> None:
        self.token_string = self._read_in_token(token_path)

    def __call__(self: "AuthToken", s: requests.Session) -> requests.Session:
        """Modify the passed in session to add token auth"""
        s.headers["Authorization"] = f"Bearer {self.token_string}"
        return s

    # Thanks to https://github.com/fermitools/jobsub_lite/blob/master/lib/tarfiles.py for this tidbit
    def _read_in_token(
        self: "AuthToken", token_path: str = get_default_token_path()
    ) -> None:
        """Read the contents of a token file from a given token path"""
        with open(token_path, "r", encoding="UTF-8") as f:
            _token_string = f.read()
            return _token_string.strip()  # Drop \n at end of token_string


class AuthCert(object):
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
