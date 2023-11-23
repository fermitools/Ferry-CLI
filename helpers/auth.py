from os import geteuid
import os.path
import sys

import requests
import requests.auth

DEFAULT_CA_DIR = "/etc/grid-security/certificates"

def get_default_token_path() -> str:
    """Get the default path where htgettoken stores bearer tokens"""
    uid = str(geteuid())
    return f"/run/user/{uid}/bt_u{uid}"

def get_default_cert_path() -> str:
    """Get the default path where cigetcert stores x509 certificates"""
    uid = str(geteuid())
    return f"/tmp/x509up_u{uid}"


class AuthToken(object):
    """This is a callable class that modifies a requests.Session object to add token
    auth"""
    def __call__(self: 'AuthToken', s: requests.Session, token_path: str = get_default_token_path()) -> requests.Session:
        self._read_in_token(token_path)
        s.headers["Authorization"] = f"Bearer {self.token_string}"
        return s

    # Thanks to https://github.com/fermitools/jobsub_lite/blob/master/lib/tarfiles.py for this tidbit
    def _read_in_token(self: 'AuthToken', token_path: str=get_default_token_path()) -> None: 
        """Read the contents of a token file from a given token path"""
        self.token_path = token_path
        with open(self.token_path, 'r', encoding="UTF-8") as f:
            self.token_string = f.read()
        self.token_string = self.token_string.strip()  # Drop \n at end of token_string




class AuthCert(object):
    """This is a callable class that modifies a requests.Session object to add X509 Certificate
    auth"""
    def __call__(self: 'AuthCert', s: requests.Session, cert_path: str = get_default_cert_path(), ca_path: str = DEFAULT_CA_DIR) -> requests.Session:
        if not os.path.exists(cert_path):
            raise FileNotFoundError(f"Cert file {cert_path} does not exist.  Please check the given path and try again.")
        if not os.path.exists(ca_path):
            raise FileNotFoundError(f"CA dir {ca_path} does not exist.  Please check the given path and try again.")
        s.cert = cert_path
        s.verify = ca_path
        return s