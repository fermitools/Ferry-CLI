# Ferry-CLI

## Requirements
* Python 3.6 or higher
  * pip3 - requests
  * pip3 - toml

## Usage - Base API  
Currently, this program is compatible with all existing ferry api calls listed on the [Ferry Docs](https://ferry.fnal.gov:8445/docs#).

To begin, simply clone the repo, and run python3 ferry.py inside the directory.

``` bash  
$ python3 ferry.py
usage: ferry.py [-h] [--cert CERT] [--capath CAPATH] [-le] [-lw] [-ep ENDPOINT_PARAMS] [-e ENDPOINT] [-w WORKFLOW] [-q]

CLI for Ferry API endpoints

optional arguments:
  -h, --help            show this help message and exit
  --cert CERT           Path to cert
  --capath CAPATH       Certificate authority path
  -le, --list_endpoints
                        List all available endpoints
  -lw, --list_workflows
                        List all available custom workflows
  -ep ENDPOINT_PARAMS, --endpoint_params ENDPOINT_PARAMS
                        List parameters for the selected endpoint
  -e ENDPOINT, --endpoint ENDPOINT
                        API endpoint and parameters
  -w WORKFLOW, --workflow WORKFLOW
                        Execute supported workflows
  -q, --quiet           Hide output
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
> Note: All responses are currently stored locally in results.json if the -q flag is not passed, for longer responses - stdout will point to the file, rather than print them in the terminal.


## Usage - Custom Workflows
Existing workflows are currently defined in workflows/supported_workflows.json
These workflow definitions do not point to the functions they run themselves, rather - this file 
enables us to convert them into argparsers. Each workflow within this file is a json object, with its name being the key, and consists of:
* description: string
* params: - an array of json objects, representing parameters and their features:
  * name : string
  * description: string
  * type: string (friendly name for the data type to use)
  * required: boolean
A simple definition within the file may look like this:
```json
{
    "getFilteredGroupInfo": {
        "description":"Returns gid, groupname, and grouptype for all groups with 'groupname' variable in its name.",
        "params": [
                {
                  "name":"groupname", 
                  "description":"Name of the group", 
                  "type":"string", 
                  "required":true
                },
            ]
      },
  }

```
  
### Workflow Flags
The workflow flags include:
[-lw/--list_workflows] and [-w/--workflow], for each of these, ferry.py will:
* --list_workflows (list all supported workflows):
 * reads supported_workflows.json and uses it to initialize a list of Workflow objects, defined in ferry.py
  > The Workflow class takes a json object as a parameter, and uses to create an argument parser - similar to how we generate endpoints from swagger.json

* --workflow (execute a custom workflow):
  * read supported_workflows.json file and uses it to initialize a single workflow, which corresponds to the workflow name
  * passes the arguments into the parser
  * if valid, finds the corresponding function - which is indexed in WORKFLOW_FUNCTIONS (dictionary constant)
    ```python
      # ferry.py
      WORKFLOW_FUNCTIONS = {
          "getFilteredGroupInfo": GetFilteredGroupInfo
      }

    ```
  * runs the corresponding workflow function
    ```python
      # ferry.py
      class Workflow:
        # ... init and stuff

        def run(self, ferry_api, args = {}):
              WORKFLOW_FUNCTIONS[self.name](self, ferry_api, args)
    
      # dcs_workflows.py
      def GetFilteredGroupInfo(self, api, args):
        # (psuedo-code)
        all_groups = api.call_endpoint("getAllGroups")
        print(f"Filtering by groupname: '{args["groupname"]}'")
        return [group for group in all_groups if group["groupname"] == args["groupname"]]
        ...

    ```
  * example: 
    ``` bash
      python3 ferry.py -w getFilteredGroupInfo --groupname=mu2e
      Called Endpoint: https://ferry.fnal.gov:8445/getAllGroups
      Filtering by groupname: 'mu2e'
      Response: [
          {
              "gid": 9914,
              "groupname": "mu2e",
              "grouptype": "UnixGroup"
          },
          {
              "gid": 0,
              "groupname": "mu2e",
              "grouptype": "BatchSuperusers"
          },
          {
              "gid": 0,
              "groupname": "mu2e",
              "grouptype": "WilsonCluster"
          }
      ]
    ```
 