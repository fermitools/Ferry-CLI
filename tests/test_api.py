import pytest
import subprocess
import time
import json
import os

TokenGetCommand = "htgettoken"
tokenDestroyCommand="htdestroytoken"
tokenDecodeCommand = "httokendecode"

tokenHost = "htvaultprod.fnal.gov" # "-a arg"
tokenUser = "fermilab"         # "-i arg"
ferryName = "hypotana"
ferryPort = 8445

# --- test helper functions

@pytest.fixture
def tokenValidCheck(passedToken):
    if "exp" in passedToken:
        if int(time.time()) < passedToken["exp"]:
            return True;
    raise ValueError(" *** Token Failure: Expired")

@pytest.fixture
def tokenDestroy():
    subprocess.run([tokenDestroyCommand])

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
    else:
        raise ValueError(" *** Token Failure: Expired")

@pytest.fixture
def getEncodedToken():
    get_token()
    uid = os.getuid()
    encodedToken = ""
    tokenPath = "/run/user/"+uid+"/bt_u"+uid
    with open(tokenPath) as file:
        encodedToken = file.read()
    return encodedToken

@pytest.fixture
# TODO: replace this with whatever the actual functionality for making calls to the endpoints is in the rest of the program via imports
def sendToEndpoint(token, endPoint):
    command = 'curl -s -H "Authorization: Bearer '+ token +'" --data-urlencode "setname=hypotana" --get https://ferry.fnal.gov:'+ str(ferryPort) +'/' + endPoint
    try:
        apiResult = json.loads(subprocess.getoutput([command])) 
    except Exception as e:
        print(" *** API Failure: Didn't get valid endpoint response")
        return False
    return apiResult

# --- tests below ----

@pytest.mark.integration
def test_token_aquisition():
    testToken = get_token()
    assert(testToken) is not False
    
@pytest.mark.integration
def test_get_capability_set():
    encodedToken = getEncodedToken()
    result = sendToEndpoint(encodedToken, "getCapabilitySet")  
    assert(result["ferry_status"]) == "success"

