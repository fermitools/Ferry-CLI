import os
from shutil import copyfile
from pathlib import Path

import pytest
from requests import Session

from helpers import auth

FAKE_CREDENTIAL_DATA = "fakecredential\n"


@pytest.fixture
def create_fake_credential(tmp_path):
    # Write a fake credential that will get deleted at the end of the calling test
    d = tmp_path / "fake_cred_dir"
    d.mkdir()
    t = d / "fake_cred_file"
    t.write_text(FAKE_CREDENTIAL_DATA)
    return str(t.absolute())  # Return the string since that's what we care about


@pytest.fixture
def token_file_name(monkeypatch):
    monkeypatch.setattr(auth, "geteuid", lambda: 42)
    return auth.default_token_file_name()


@pytest.mark.unit
def test_read_in_token(create_fake_credential):
    assert auth.read_in_token(create_fake_credential) == FAKE_CREDENTIAL_DATA.strip()


class TestGetDefaultTokenString:
    @pytest.mark.unit
    def test_get_default_token_string_bearer_token_val(self, monkeypatch):
        monkeypatch.setenv("BEARER_TOKEN", "randomtokenstring")
        assert auth.get_default_token_string() == "randomtokenstring"

    @pytest.mark.unit
    def test_get_default_token_string_bearer_token_file(
        self, create_fake_credential, monkeypatch
    ):
        monkeypatch.delenv("BEARER_TOKEN", raising=False)
        monkeypatch.setenv("BEARER_TOKEN_FILE", create_fake_credential)
        assert auth.get_default_token_string() == FAKE_CREDENTIAL_DATA.strip()

    @pytest.mark.unit
    def test_get_default_token_string_xdg_runtime_dir(
        self, create_fake_credential, token_file_name, monkeypatch
    ):
        fake_credential = create_fake_credential
        fake_cred_dir = str(Path(fake_credential).parent)
        copyfile(fake_credential, f"{fake_cred_dir}/{token_file_name}")
        monkeypatch.delenv("BEARER_TOKEN", raising=False)
        monkeypatch.delenv("BEARER_TOKEN_FILE", raising=False)
        monkeypatch.setenv("XDG_RUNTIME_DIR", fake_cred_dir)
        assert auth.get_default_token_string() == FAKE_CREDENTIAL_DATA.strip()

    @pytest.mark.unit
    def test_get_default_token_string_fallthrough(
        self, create_fake_credential, token_file_name, monkeypatch
    ):
        monkeypatch.delenv("BEARER_TOKEN", raising=False)
        monkeypatch.delenv("BEARER_TOKEN_FILE", raising=False)
        monkeypatch.delenv("XDG_RUNTIME_DIR", raising=False)
        fake_credential = create_fake_credential
        copyfile(fake_credential, f"/tmp/{token_file_name}")
        assert auth.get_default_token_string() == FAKE_CREDENTIAL_DATA.strip()


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
        assert (
            auth_session.headers["Authorization"]
            == f"Bearer {FAKE_CREDENTIAL_DATA.strip()}"
        )

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
