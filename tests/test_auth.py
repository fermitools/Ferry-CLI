import os
from pathlib import Path
import unittest.mock

import pytest
from requests import Session

from helpers import auth

FAKE_CREDENTIAL_DATA = 'fakecredential'

@pytest.fixture
def create_fake_credential(tmp_path):
    # Write a fake credential that will get deleted at the end of the calling test
    d = tmp_path / "fake_cred_dir"
    d.mkdir()
    t = d / "fake_cred_file"
    t.write_text(FAKE_CREDENTIAL_DATA)
    return t.absolute()


@pytest.mark.unit
def test_get_default_token_location():
    with unittest.mock.patch.object(auth, 'geteuid') as m:
        m.return_value = 42
        assert auth.get_default_token_location()== f"/run/user/42/bt_u42"

@pytest.mark.unit
def test_get_default_cert_location():
    with unittest.mock.patch.object(auth, 'geteuid') as m:
        m.return_value = 42
        assert auth.get_default_cert_location()== f"/tmp/x509up_u42"

@pytest.mark.unit
def test_AuthToken(create_fake_credential):
    s = Session()
    authorizer = auth.AuthToken()
    auth_session = authorizer(s, create_fake_credential)
    assert auth_session.headers["Authorization"] == f"Bearer {FAKE_CREDENTIAL_DATA}"


@pytest.mark.unit
def test_AuthCert(create_fake_credential):
    s = Session()
    authorizer = auth.AuthCert()
    fake_cert = create_fake_credential
    auth_session = authorizer(s, cert_location=fake_cert)
    assert Path(auth_session.cert).read_text() == FAKE_CREDENTIAL_DATA
    assert auth_session.verify == auth.DEFAULT_CA_DIR 


