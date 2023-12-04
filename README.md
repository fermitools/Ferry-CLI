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
usage: ferry.py [-h] [--cert CERT] [--capath CAPATH] [-le] [-lw] [-ep ENDPOINT_PARAMS] [-wp WORKFLOW_PARAMS] [-e ENDPOINT] [-w WORKFLOW] [-q]

CLI for Ferry API endpoints

optional arguments:
  -h, --help            show this help message and exit
  --cert CERT           Path to cert
  --capath CAPATH       Certificate authority path
  -le, --list_endpoints
                        List all available endpoints
  -lw, --list_workflows
                        List all supported custom workflows
  -ep ENDPOINT_PARAMS, --endpoint_params ENDPOINT_PARAMS
                        List parameters for the specified endpoint
  -wp WORKFLOW_PARAMS, --workflow_params WORKFLOW_PARAMS
                        List parameters for the supported workflow
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

Listing parameters for endpoint: https://{ferry_url}/getUserInfo

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

Calling: "curl --cert /tmp/x509up_u12345 --capath /etc/grid-security/certificates https://{ferry_url}/getUserInfo?username=johndoe"

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
Existing workflows are defined in helpers.supported_workflows.*
These workflow definitions inherit the Abstracted Workflow class, and follow a strict convention in order to achieve uniformity and simplicity. These "workflows" are extended functions, which may run a series of ferry calls in sequence in order to simply achieve a goal that generally requires more complex logic.

Each custom workflow should be defined as a separate class, see below for example implementation:
* name: string - name of workflow
* description: string - what does the workflow do?
* params: - an array of json objects, representing parameters and their features:
  * name : string
  * description: string
  * type: string (friendly name for the data type to use)
  * required: boolean

* run(api, args): inherited function - this is where your logic goes 

A simple definition within the file may look like this:
```python

from helpers.customs import Workflow

class GetFilteredGroupInfo(Workflow):
    def __init__(self):
        self.name = "getFilteredGroupInfo"
        self.method = "GET"
        self.description = "Returns gid, groupname, and grouptype for all groups with 'groupname' variable in its name."
        self.params = [
                {
                    "name":"groupname", 
                    "description":"Name of the group", 
                    "type":"string", 
                    "required":True
                }
            ]
        super().__init__(self)
        
    # Gets all the groups, filter json output by group name, returns filtered json list
    def run(self, api, args):
        group_json = api.call_endpoint("getAllGroups")
        if not group_json:
            print(f"Failed'")
            exit(1)
        print(f"Recieved successful response")
        print(f"Filtering by groupname: '{args['groupname']}'")
        group_info = [entry for entry in group_json["ferry_output"] if entry["groupname"] == args["groupname"]]
        return group_info
```

  
### Workflow Flags
The workflow flags include:
[-lw/--list_workflows], [-wp/--workflow_params] and [-w/--workflow], for each of these, ferry.py will:
* --list_workflows (list all supported workflows):
* --workflow_params (list specified workflow parameters):
* --workflow (execute a custom workflow):
  * passes arguments into the parser
  * if valid, finds the corresponding function - which is indexed in SUPPORTED_WORKFLOWS (dictionary constant)
    ```python
      # helpers.supported_workflows.__init__.py
      
      # Import custom workflow modules
      from helpers.supported_workflows.GetFilteredGroupInfo import GetFilteredGroupInfo

      # Index them here
      SUPPORTED_WORKFLOWS = {
          "getFilteredGroupInfo": GetFilteredGroupInfo,
      }

    ```
  * runs the corresponding workflow function
    ```python
      # helpers.customs.py
      class Workflow(ABC):
        # ... init and stuff

        @abstractmethod
        def run(self, api:FerryAPI, args):
            # This method should be implemented by all subclasses
            pass
    ```
  * example: 
    ``` bash
      python3 ferry.py -w getFilteredGroupInfo --groupname=mu2e
      Called Endpoint: https://{ferry_url}/getAllGroups
      Recieved successful response
      Filtering by groupname: 'mu2e'
      Response: [
          {
              "gid": 1,
              "groupname": "group 1",
              "grouptype": "group 1 type"
          },
          ...
          {
              "gid": 4,
              "groupname": "group 4",
              "grouptype": "group 4 type"
          },
      ]
    ```
 