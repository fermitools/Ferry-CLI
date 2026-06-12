from functools import partial
import pytest
import subprocess
import time
from typing import Dict, Any
import json
import os

from ferry_cli.helpers.api import FerryAPI, tempfile
from ferry_cli.helpers.auth import AuthToken
from tests.conftest import fakeAuth

TokenGetCommand = "htgettoken"
tokenDestroyCommand = "htdestroytoken"
tokenDecodeCommand = "htdecodetoken"

tokenHost = "htvaultprod.fnal.gov"  # "-a arg"
tokenUser = "fermilab"  # "-i arg"
ferryName = "hypotana"
ferryPort = 8445
FERRY_DEV_SERVER = "https://ferrydev.fnal.gov"
FERRY_DEV_PORT = 8447


# --- fixtures


@pytest.fixture
def get_token(monkeypatch, tmp_path):
    # Set up temporary area for token to live
    token_file = tmp_path / "tokenfile"
    token_file.touch()
    old_bearer_token_file = os.getenv("BEARER_TOKEN_FILE", None)
    monkeypatch.setenv("BEARER_TOKEN_FILE", str(token_file.absolute()))

    # Get our token
    proc = subprocess.run([TokenGetCommand, "-a", tokenHost, "-i", tokenUser])
    if proc.returncode != 0:
        raise ValueError(
            f"{TokenGetCommand} failed.  Please try running it manually for more details"
        )

    # Decode and validate the token
    tokenObject = {}
    tokenDecoding = subprocess.getoutput([tokenDecodeCommand])

    try:
        tokenObject = json.loads(tokenDecoding)
    except ValueError as ve:
        print(" *** Token Failure: Didn't get valid JWT")
        raise ve

    tokenValidCheck(tokenObject)
    yield tokenObject

    # Set the environment back
    if old_bearer_token_file:
        os.environ["BEARER_TOKEN_FILE"] = old_bearer_token_file


@pytest.fixture
def get_token_path():
    return os.getenv("BEARER_TOKEN_FILE", f"/run/user/{os.getuid()}/bt_u{os.getuid()}")


@pytest.fixture
def getEncodedToken(get_token, get_token_path):
    with open(get_token_path) as file:
        return file.read().strip()


@pytest.fixture(scope="function")
def sendToEndpoint(get_token):
    token_auth = AuthToken()

    def _sendToEndpoint(
        token,
        endPoint,
        method: str = "get",
        data: Dict[Any, Any] = {},
        headers: Dict[str, Any] = {},
        params: Dict[Any, Any] = {},
    ):
        api = FerryAPI(f"{FERRY_DEV_SERVER}:{FERRY_DEV_PORT}/", token_auth)
        try:
            apiResult = api.call_endpoint(
                endpoint=endPoint,
                method=method,
                data=data,
                headers=headers,
                params=params,
            )
        except Exception as e:
            print(" *** API Failure: Didn't get valid endpoint response")
            raise
        return apiResult

    return _sendToEndpoint


@pytest.fixture
def reload_import_tempfile(monkeypatch):
    from importlib import reload

    yield
    monkeypatch.undo()
    reload(tempfile)


# --- tests below ----


@pytest.mark.integration
def test_token_aquisition(get_token):
    assert get_token is not False


@pytest.mark.integration
def test_get_capability_set(getEncodedToken, sendToEndpoint):
    result = sendToEndpoint(getEncodedToken, "getCapabilitySet")
    assert (result["ferry_status"]) == "success"


@pytest.mark.integration
def test_getAllGroups(getEncodedToken, sendToEndpoint):
    result = sendToEndpoint(getEncodedToken, "getAllGroups")
    assert (result["ferry_status"]) == "success"
    assert result["ferry_output"]  # Make sure we got non-empty result


class TestGetLatestSwaggerFile:
    @classmethod
    def setup_class(cls):
        cls.auth = fakeAuth()
        cls.base_url = "https://test.example.com"

    @pytest.mark.unit
    def test_dryrun(self, monkeypatch, tmp_path, capsys):
        tmp = tmp_path
        monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp))
        api = FerryAPI(base_url=self.base_url, authorizer=self.auth, dryrun=True)
        api.get_latest_swagger_file()
        captured = capsys.readouterr()
        assert "Dryrun: skipping swagger.json fetching" in captured.out
        assert not api.swagger_file.exists()

    @pytest.mark.integration
    def test_regular(self, monkeypatch, tmp_path, capsys, get_token):
        tmp = tmp_path
        monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp))
        api = FerryAPI(
            base_url=f"{FERRY_DEV_SERVER}:{FERRY_DEV_PORT}/", authorizer=AuthToken()
        )
        api.get_latest_swagger_file()
        captured = capsys.readouterr()
        assert api.swagger_file.exists()


class TestSetSwaggerFile:
    @classmethod
    def setup_class(cls):
        _auth = fakeAuth()
        cls.api = FerryAPI(
            base_url="https://test.example.com", authorizer=_auth, dryrun=True
        )

    @pytest.mark.unit
    def test_set_swagger_file_configdir(self, monkeypatch, tmp_path):
        tmp = tmp_path
        monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))

        filename = self.api._swagger_filename()
        assert (
            self.api._set_swagger_file().resolve()
            == (tmp / "ferry_cli" / filename).resolve()
        )

    @pytest.mark.unit
    def test_set_swagger_file_tmpdir(
        self, monkeypatch, tmp_path, reload_import_tempfile
    ):
        from importlib import reload

        tmp = tmp_path
        monkeypatch.setenv("TMPDIR", str(tmp))
        monkeypatch.delenv("HOME")
        monkeypatch.delenv("XDG_CONFIG_HOME", raising=False)

        reload(tempfile)

        filename = self.api._swagger_filename()
        assert self.api._set_swagger_file().resolve() == tmp / filename


@pytest.mark.unit
def test_swagger_filename():
    _auth = fakeAuth()
    api = FerryAPI(base_url="https://test.example.com", authorizer=_auth, dryrun=True)
    # Hash should be created from "https://test.example.com/swagger/swagger.json"
    assert api._swagger_filename() == f"swagger_9da5f7c34792d7ef.json"


# --- test helper functions


def tokenValidCheck(passedToken):
    if "exp" in passedToken:
        if int(time.time()) < passedToken["exp"]:
            return
    raise ValueError(" *** Token Failure: Expired")


def tokenDestroy():
    subprocess.run([tokenDestroyCommand])
