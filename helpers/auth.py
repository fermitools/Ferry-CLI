from os import geteuid

import requests
import requests.auth


DEFAULT_CA_DIR = "/etc/grid-security/certificates"

def get_default_token_location() -> str:
    """Get the default location where htgettoken stores bearer tokens"""
    uid = str(geteuid())
    return f"/run/user/{uid}/bt_u{uid}"

def get_default_cert_location() -> str:
    """Get the default location where cigetcert stores x509 certificates"""
    uid = str(geteuid())
    return f"/tmp/x509up_u{uid}"


class AuthToken(object):
    """This is a callable class that modifies a requests.Session object to add token
    auth"""
    def __call__(self: 'AuthToken', s: requests.Session, token_location: str = get_default_token_location()) -> requests.Session:
        self._read_in_token(token_location)
        s.headers["Authorization"] = f"Bearer {self.token_string}"
        return s

    # Thanks to https://github.com/fermitools/jobsub_lite/blob/master/lib/tarfiles.py for this tidbit
    def _read_in_token(self: 'AuthToken', token_location: str=get_default_token_location()) -> None: 
        """Read the contents of a token file from a given token location"""
        self.token_location = token_location
        with open(self.token_location, 'r', encoding="UTF-8") as f:
            self.token_string = f.read()
        self.token_string = self.token_string.strip()  # Drop \n at end of token_string



class AuthCert(object):
    """This is a callable class that modifies a requests.Session object to add X509 Certificate
    auth"""
    def __call__(self: 'AuthCert', s: requests.Session, cert_location: str = get_default_cert_location(), ca_path: str = DEFAULT_CA_DIR) -> requests.Session:
        s.cert = cert_location
        s.verify = ca_path
        return s