import pytest
import subprocess
import time
from typing import Dict, Any
import json
import os

from ferry_cli.helpers.api import FerryAPI
from ferry_cli.helpers.auth import AuthToken

TokenGetCommand = "htgettoken"
tokenDestroyCommand = "htdestroytoken"
tokenDecodeCommand = "httokendecode"

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
    uid = os.getuid()
    token_path = f"/run/user/{uid}/bt_u{uid}"
    return token_path


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


# --- test helper functions


def tokenValidCheck(passedToken):
    if "exp" in passedToken:
        if int(time.time()) < passedToken["exp"]:
            return
    raise ValueError(" *** Token Failure: Expired")


def tokenDestroy():
    subprocess.run([tokenDestroyCommand])
