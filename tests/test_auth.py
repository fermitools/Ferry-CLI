import os
from pathlib import Path

import pytest
from requests import Session

from helpers import auth

FAKE_CREDENTIAL_DATA = "fakecredential"


@pytest.fixture
def create_fake_credential(tmp_path):
    # Write a fake credential that will get deleted at the end of the calling test
    d = tmp_path / "fake_cred_dir"
    d.mkdir()
    t = d / "fake_cred_file"
    t.write_text(FAKE_CREDENTIAL_DATA)
    return t.absolute()


class TestGetDefaultTokenPath:
    @pytest.mark.unit
    def test_get_default_token_path_env(self, monkeypatch):
        monkeypatch.setenv("BEARER_TOKEN_FILE", "randompathtotoken")
        assert auth.get_default_token_path() == "randompathtotoken"

    @pytest.mark.unit
    def test_get_default_token_path(self, monkeypatch):
        monkeypatch.delenv("BEARER_TOKEN_FILE", raising=False)
        monkeypatch.setattr(auth, "geteuid", lambda: 42)
        assert auth.get_default_token_path() == f"/run/user/42/bt_u42"


class TestGetDefaultCertPath:
    @pytest.mark.unit
    def test_get_default_cert_path_env(self, monkeypatch):
        monkeypatch.setenv("X509_USER_PROXY", "randompathtocert")
        assert auth.get_default_cert_path() == "randompathtocert"

    @pytest.mark.unit
    def test_get_default_cert_path(self, monkeypatch):
        monkeypatch.delenv("X509_USER_PROXY", raising=False)
        monkeypatch.setattr(auth, "geteuid", lambda: 42)
        assert auth.get_default_cert_path() == f"/tmp/x509up_u42"


class TestAuthToken:
    @pytest.mark.unit
    def test_AuthToken(self, create_fake_credential):
        s = Session()
        authorizer = auth.AuthToken(create_fake_credential)
        auth_session = authorizer(s)
        assert auth_session.headers["Authorization"] == f"Bearer {FAKE_CREDENTIAL_DATA}"

    @pytest.mark.unit
    def test_AuthToken_bad(self):
        s = Session()
        with pytest.raises(FileNotFoundError):
            auth.AuthToken(token_path="thispathdoesntexist")


class TestAuthCert:
    @pytest.mark.unit
    def test_AuthCert(self, create_fake_credential):
        s = Session()
        authorizer = auth.AuthCert(cert_path=create_fake_credential)
        auth_session = authorizer(s)
        assert Path(auth_session.cert).read_text() == FAKE_CREDENTIAL_DATA
        assert auth_session.verify == auth.DEFAULT_CA_DIR

    @pytest.mark.unit
    def test_AuthCert_bad(self):
        s = Session()
        with pytest.raises(FileNotFoundError):
            auth.AuthCert(cert_path="thispathdoesntexist")

    @pytest.mark.unit
    def test_AuthCert_capath_bad(self):
        s = Session()
        with pytest.raises(FileNotFoundError):
            auth.AuthCert(ca_path="thispathdoesntexist")
