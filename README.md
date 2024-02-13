# Ferry-CLI

## REQUIREMENTS
* Bearer token (htgettoken) or x509 user proxy for authorization

AND

* Python 3.6  or higher + pip with the following libraries:
	certifi>=2023.11.17
	charset-normalizer>=3.3.2
	idna>=3.4
	requests>=2.31.0
	urllib3>=2.1.0

OR

* [spack](https://github.com/FNALssi/fermi-spack-tools/wiki) package manager with the [scd_recipes](https://github.com/marcmengel/scd_recipes) repository
  * See .spack/package.py for package information

## INSTALL
Install is simple, and can be done via source, pip, or spack:

#### Using pip:

* Simply Run:
	``` bash
		# using https
		pip install git+https://github.com/fermitools/Ferry-CLI.git

		# using ssh
		pip install git@github.com:fermitools/Ferry-CLI.git
	```

* If you wish to contribute to this project, or run a local copy:
	``` bash
		git clone https://github.com/fermitools/Ferry-CLI.git
		cd Ferry-CLI

		# Uncomment if you wish to use a virtual environment
		# python3 -m venv .venv
		# source .venv/bin/activate

		pip install .

		# If you don't wish to use pip or spack,
		# you can create a symlink to the executable:
		sudo ln -s /path/to/Ferry-CLI/bin/ferry-cli /usr/bin/ferry-cli

	```

#### Using Spack:
If not already done, install spack, with the scd_recipes repo
* Guide: [spack setup](https://github.com/FNALssi/fermi-spack-tools/wiki)

You can now either create a new spack environment, or add ferry-cli to an existing environment:
```bash
# Uncomment to use in a custom spack environment
# spack env create ferry_cli_env
# spack env activate ferry_cli_env
# spack add ferry-cli

spack install ferry-cli
spack load ferry-cli
```


## AUTHORIZE
#### htgettoken

The ferry-cli is designed to make setup as easy as possible. Before you begin, ensure that you have htgettoken set up.

Once this is done, the following script will ensure you have everything you need to run the CLI:
```
httokensh -i fermilab -a htvaultprod.fnal.gov -- /bin/bash

# then simply run
ferry-cli ARGS
```
> If a token is not pre-defined, you can also include -a token --token-path=/tmp/bt_u{uid} to your args

If you wish to use a custom "**token-path**" for your token, you can set the standard token flags as needed.
> The CLI is configured to look for a token by default, and follows the WLCG Bearer Token Discovery standard here: https://zenodo.org/records/3937438, but this can be overridden with a custom path via --token-path={your_custom_path}.

If a token is not found in the default or custom paths, the CLI will return an error stating that an authentication method is required.

#### X509 USER PROXY
If you wish to use a cert, you can do so by running:
```bash
kinit $USER
kx509
ferry-cli -a cert --cert_path=/tmp/x509up_u{uid} --ca_path=/etc/grid-security/certificates ARGS
```
> The paths above are the default paths. The cli will check there by default and at **$X509_USER_PROXY** if defined.


## USAGE

Currently, this program is compatible with all existing ferry api calls listed on the [Ferry Docs](https://ferry.fnal.gov:8445/docs#).


To begin, simply run:  ferry-cli

``` bash
$ ferry-cli
usage: ferry-cli [-h] [-a AUTH_METHOD] [--token-path TOKEN_PATH | --cert-path CERT_PATH] [--ca-path CA_PATH] [-d] [-q] [-u] [--filter FILTER] [-le] [-lw] [-ep ENDPOINT_PARAMS] [-wp WORKFLOW_PARAMS] [-e ENDPOINT] [-w WORKFLOW]

CLI for Ferry API endpoints

optional arguments:
  -h, --help            show this help message and exit
  -a AUTH_METHOD, --auth-method AUTH_METHOD
                        Auth method for FERRY request
  --token-path TOKEN_PATH
                        Path to bearer token
  --cert-path CERT_PATH
                        Path to cert
  --ca-path CA_PATH     Certificate authority path
  -d, --debug           Turn on debugging
  -q, --quiet           Hide output
  -u, --update          Get latest swagger file
  --support_email       Get Ferry CLI support emails
  --version             Get Ferry CLI version
  --filter FILTER       (string) Use to filter results on -le and -lw flags
  -le, --list_endpoints
                        List all available endpoints
  -lw, --list_workflows
                        List all supported custom workflows
  -ep ENDPOINT_PARAMS, --endpoint_params ENDPOINT_PARAMS
                        List parameters for the selected endpoint
  -wp WORKFLOW_PARAMS, --workflow_params WORKFLOW_PARAMS
                        List parameters for the supported workflow
  -e ENDPOINT, --endpoint ENDPOINT
                        API endpoint and parameters
  -w WORKFLOW, --workflow WORKFLOW
                        Execute supported workflows
```
---
## Safeguards
Not all ferry endpoints should be used by DCS, or other groups that may be using this. Therefore:
* safeguards.py is where you can store information for users regarding the proper steps to achieve a goal.
* endpoints that are listed in safeguards.py will not be called, rather - they will print out a message for the user listing the correct action to take:
```bash
$ ferry-cli -e createUser

              SAFEGUARDED: DCS Should NOT be using this call.

              Use this form to get a UID/GID if needed: (LINK_TO_FORM)
              Then do whatever you needed to do.

```
> This holds true when running -e or -ep


## Example CLI Usage:

### List Endpoints

``` bash
$ ferry-cli -le

Using token auth

                      Listing all supported endpoints:

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

### List Endpoints (with filter)

``` bash
$ ferry-cli -le --filter=sync

Using token auth

                      Listing all supported endpoints (filtering for "sync"):

syncLdapWithFerry                            (PUT) | Synchronize all USER LDAP data to FERRY with FERRY as the
                                                   | source of truth. Does NOT synchronize capability sets and
                                                   | scopes. 1. Removes all records in LDAP which have no
                                                   | corresponding record in FERRY, or are not active users in
                                                   | FERRY. 2. Adds all active FERRY users to LDAP which are
                                                   | missing from LDAP. 3. Verifies the capability sets in LDAP
                                                   | are set properly for each user, per their FQANs, correcting
                                                   | LDAP as needed.

```

---

### List endpoint parameters/args:
``` bash
$ ferry-cli -ep getUserInfo

Listing parameters for endpoint: https://{ferry_url}/getUserInfo

usage: ferry-cli [-h] [--username USERNAME] [--uid UID] [--vopersonid VOPERSONID]

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
$ ferry-cli -e getUserInfo --username=johndoe

Using token auth

Calling Endpoint: https://{ferry_url}/getUserInfo
Called Endpoint: https://{ferry_url}/getUserInfo?username=johndoe
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

* run(api, args): inherited function - this is where your logic should go

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
* --list_workflows (list all supported workflows)
  > Note: you may use the --filter flag with this action:
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
      ferry-cli -w getFilteredGroupInfo --groupname=mu2e
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
