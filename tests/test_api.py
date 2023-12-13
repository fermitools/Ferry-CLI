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
def get_token():
    subprocess.run([TokenGetCommand, "-a", tokenHost, "-i", tokenUser])

    tokenObject = {}
    tokenDecoding = subprocess.getoutput([tokenDecodeCommand])

    try:
        tokenObject = json.loads(tokenDecoding)
    except ValueError as ve:
        print(" *** Token Failure: Didn't get valid JWT")
        raise ve

    if tokenValidCheck(tokenObject):
        return tokenObject


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
            return True
    raise ValueError(" *** Token Failure: Expired")


def tokenDestroy():
    subprocess.run([tokenDestroyCommand])
