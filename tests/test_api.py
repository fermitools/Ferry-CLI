import pytest
import subprocess
import time
import json
import os

TokenGetCommand = "htgettoken"
tokenDestroyCommand = "htdestroytoken"
tokenDecodeCommand = "httokendecode"

tokenHost = "htvaultprod.fnal.gov"  # "-a arg"
tokenUser = "fermilab"  # "-i arg"
ferryName = "hypotana"
ferryPort = 8445


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
# TODO: replace this with whatever the actual functionality for making calls to the endpoints is in the rest of the program via imports
def sendToEndpoint(get_token):
    def _sendToEndpoint(token, endPoint):
        command = (
            'curl -s -H "Authorization: Bearer '
            + token
            + '" --data-urlencode "setname=hypotana" --get https://ferry.fnal.gov:'
            + str(ferryPort)
            + "/"
            + endPoint
        )
        try:
            apiResult = json.loads(subprocess.getoutput([command]))
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


# --- test helper functions


def tokenValidCheck(passedToken):
    if "exp" in passedToken:
        if int(time.time()) < passedToken["exp"]:
            return
    raise ValueError(" *** Token Failure: Expired")


def tokenDestroy():
    subprocess.run([tokenDestroyCommand])
