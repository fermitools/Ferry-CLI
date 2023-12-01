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

def tokenValidCheck(passedToken):
    if "exp" in passedToken:
        if int(time.time()) < passedToken["exp"]:
            return True;
    print(" *** Token Failure: Token expired")
    return False;

def tokenDestroy():
    subprocess.run([tokenDestroyCommand])

def get_token():
    subprocess.run([TokenGetCommand, "-a", tokenHost, "-i", tokenUser])

    tokenObject = {}
    tokenDecoding = subprocess.getoutput([tokenDecodeCommand])
    
    try:
        tokenObject = json.loads(tokenDecoding)
    except ValueError as ve:
        print(" *** Token Failure: didn't get valid JWT")
        return False
    
    if tokenValidCheck(tokenObject):
        return tokenObject
    else:
        return False

def getEncodedToken():
    get_token()
    uid = subprocess.getoutput("id -u")
    encodedToken = ""
    tokenPath = "/run/user/"+uid+"/bt_u"+uid
    with open(tokenPath) as file:
        encodedToken = file.read()
    return encodedToken

# TODO: replace this with whatever the actual functionality for making calls to the endpoints is in the rest of the program via imports
def sendToEndpoint(token, endPoint):
    command = 'curl -s -H "Authorization: Bearer '+ token +'" --data-urlencode "setname=hypotana" --get https://ferry.fnal.gov:'+ str(ferryPort) +'/' + endPoint
    try:
        apiResult = json.loads(subprocess.getoutput([command])) 
    except Exception as e:
        print(" *** API Failure: didn't get valid endpoint response")
        return False
    return apiResult

# --- tests below ----

def test_token_aquisition():
    testToken = get_token()
    assert(testToken) is not False

def test_get_capability_set():
    encodedToken = getEncodedToken()
    result = sendToEndpoint(encodedToken, "getCapabilitySet")  
    assert(result["ferry_status"]) == "success"

