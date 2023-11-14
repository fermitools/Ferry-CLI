# Ferry-CLI

## Usage  
Currently, this program is compatible with all existing ferry api calls listed on the [Ferry Docs](https://ferry.fnal.gov:8445/docs#).

To begin, simply clone the repo, and run python3 ferry.py inside the directory.

``` bash  
$ python3 ferry.py  
usage: ferry.py [-h] [--cert CERT] [--capath CAPATH] [-l] [-ep ENDPOINT_PARAMS] [-e ENDPOINT]

CLI for Ferry API endpoints

optional arguments:
  -h, --help            show this help message and exit
  --cert CERT           Path to cert (default: /tmp/x509up_u$UID)
  --capath CAPATH       Certificate authority path (default: /etc/grid-security/certificates)
  -l, --list_endpoints  List all available endpoints
  -ep ENDPOINT_PARAMS, --endpoint_params ENDPOINT_PARAMS
                        List parameters for the selected endpoint
  -e ENDPOINT, --endpoint ENDPOINT
                        API endpoint and parameters  
```
---
## Safeguards
Not all ferry endpoints should be used by DCS, or other groups that may be using this. Therefore:
* safeguards.py is where you can store information for users regarding the proper steps to achieve a goal.
* endpoints that are listed in safeguards.py will not be called, rather - they will print out a message for the user listing the correct action to take:
```bash
$ python3 ferry.py -e createUser

              SAFEGUARDED: DCS Should NOT be using this call.
              
              Use this form to get a UID/GID if needed: (LINK_TO_FORM)
              Then do whatever you needed to do.

```
> This holds true when running -e or -ep


## Example CLI Usage:

### List Endpoints

``` bash
$ python3 ferry.py -l

Listing all available endpoints:

IsUserLeaderOfGroup                          (GET) | Returns if the user is the leader of the group.


IsUserMemberOfGroup                          (GET) | Returns if the user belongs to the specified group.


addCapabilitySetToFQAN                       (PUT) | Associates a capability set with a FQAN.  A FQAN can have
                                                   | one and only one associated capability sets. This method
                                                   | will override any prior setting. LDAP records for all users
                                                   | of the FQAN are immediately updated. That update could take
                                                   | a while.
... (Continues)

```

---

### List endpoint parameters/args:
``` bash
$ python3 ferry.py -ep getUserInfo

Listing parameters for endpoint: https://ferry.fnal.gov:8445/getUserInfo

usage: ferry.py [-h] [--username USERNAME] [--uid UID] [--vopersonid VOPERSONID]

getUserInfo (GET) | For a specific user, returns the entity attributes. You must | supply ONE of username or uid or vopersonid.

optional arguments:
  -h, --help            show this help message and exit
  --username USERNAME   (string) | user for whom the attributes are to be returned
  --uid UID             (integer) | uid for whom the attributes are to be returned
  --vopersonid VOPERSONID
                        (string) | UUID for whom the attributes are to be returned
```

### Call an endpoint:
``` bash
$ python3 ferry.py -e getUserInfo --username=johndoe

Endpoint: getUserInfo

Arguments: [
   username=johndoe
]

Calling: "curl --cert /tmp/x509up_u12345 --capath /etc/grid-security/certificates https://ferry.fnal.gov:8445/getUserInfo?username=johndoe"

Response: {
    "ferry_status": "success",
    "ferry_error": [],
    "ferry_output": {
        "banned": false,
        "expirationdate": "2038-01-01T00:00:00Z",
        "fullname": "John Doe",
        "groupaccount": false,
        "status": true,
        "uid": 54321,
        "vopersonid": "00000000-0000-0000-0000-000000000000"
    }
}

```
> Note: All responses are stored locally in results.json, longer responses will point to the file, rather than print them in the terminal.
