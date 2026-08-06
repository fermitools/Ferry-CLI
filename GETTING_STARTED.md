# Getting Started with Ferry-CLI

This guide provides examples for using the Ferry CLI to interact with the Ferry API endpoints.

## Table of Contents
- [Installation](#installation)
- [Configuration](#configuration)
- [Authentication](#authentication)
- [Basic Commands](#basic-commands)
- [Working with Endpoints](#working-with-endpoints)
- [Working with Workflows](#working-with-workflows)
- [Advanced Options](#advanced-options)

---

## Installation

Install ferry-cli using pip:

```bash
# Using https
pip install git+https://github.com/fermitools/Ferry-CLI.git

# Using ssh (for development)
pip install git@github.com:fermitools/Ferry-CLI.git
```

Or clone and install locally:

```bash
git clone https://github.com/fermitools/Ferry-CLI.git
cd Ferry-CLI
pip install .
```

---

## Configuration

The first time you run `ferry-cli`, it will prompt you to create a configuration file interactively:

```bash
ferry-cli
```

This creates a config file at `~/.config/ferry_cli/config.ini` (or `$XDG_CONFIG_HOME/ferry_cli/config.ini`).

You can also manually create the config file:

```ini
[api]
base_url = https://ferry.hostname.domain:8445/
```

---

## Authentication

Ferry-CLI supports two authentication methods:

### Token Authentication (Default)

Ensure you have a valid bearer token that can access your FERRY instance. For Fermilab users, see the FIFE wiki for more details.

```bash
# Then use ferry-cli (token is auto-detected)
ferry-cli [options]
```
The CLI follows the WLCG Bearer Token Discovery standard and looks for tokens in:
- `$BEARER_TOKEN_FILE` environment variable
- `$XDG_RUNTIME_DIR/bt_u{uid}` (default: `/tmp/bt_u{uid}`)

### Certificate Authentication

Ensure you have a valid X509 grid or VOMS proxy certificate.  This method of authentication is very rare for users, so we will not discuss how to obtain one here.

```bash
# Use certificate auth with ferry-cli
ferry-cli -a cert
```

---

## Basic Commands

### Show Help

```bash
# Show main help
ferry-cli --help

# Show specific endpoint help
ferry-cli -ep <endpoint-name>
```

### List Available Endpoints

```bash
# List all endpoints
ferry-cli -le

# List endpoints with filter
ferry-cli -le --filter=sync
```

### List Supported Workflows

```bash
# List all workflows
ferry-cli -lw

# List workflows with filter
ferry-cli -lw --filter=group
```

---

## Working with Endpoints

### Get Endpoint Parameters

```bash
# Show parameters for a specific endpoint
ferry-cli -ep getUserInfo
```

Output:
```
usage: ferry-cli [-h] [--username USERNAME] [--uid UID] [--vopersonid VOPERSONID]

getUserInfo (GET) | For a specific user, returns the entity attributes.
You must supply ONE of username or uid or vopersonid.

optional arguments:
  -h, --help            show this help message and exit
  --username USERNAME   (string) | user for whom the attributes are to be returned
  --uid UID             (integer) | uid for whom the attributes are to be returned
  --vopersonid VOPERSONID
                        (string) | UUID for whom the attributes are to be returned
```

### Call an Endpoint

The CLI automatically converts endpoint names to camelCase:

```bash
# Get user info by username
ferry-cli -e getUserInfo --username=username

# Get user info by uid
ferry-cli -e getUserInfo --uid=12345
```


### Filter Endpoints

Use the `--filter` flag to search for specific endpoints. Case is ignored:

```bash
# List only endpoints containing "sync"
ferry-cli -le --filter=sync

# Get parameters for filtered endpoints
ferry-cli -ep syncLdapWithFerry
```

---

## Working with Workflows

### List Available Workflows

```bash
ferry-cli -lw
```

Available workflows include:
- `cloneResource` - Clone an existing resource
- `getFilteredGroupInfo` - Get filtered group information
- `newCapabilitySet` - Create a new capability set

### Get Workflow Parameters

```bash
# Show parameters for a specific workflow
ferry-cli -wp getFilteredGroupInfo
```

### Execute a Workflow

```bash
# Get filtered group info
ferry-cli -w getFilteredGroupInfo --groupname=mygroup

# Clone a resource
ferry-cli -w cloneResource --clone=original_resource --new_resource=new_resource --unitname=unit_name

# Create new capability set
ferry-cli -w newCapabilitySet \
  --groupname=groupname \
  --gid=12345 \
  --unitname=unitname \
  --fqan=/somegroup/Role=Rolename/Capability=NULL \
  --setname=setname \
  --scopes_pattern="scope1,scope2"
```

---

## Advanced Options

### Output Options

```bash
# Save output to a file
ferry-cli -e getUserInfo --username=username --output=/path/to/output.json

# Quiet mode (no output)
ferry-cli -e getUserInfo --username=username -q

# Debug mode (show detailed info)
ferry-cli -e getUserInfo --username=username -d
```

### Dry Run Mode

Show API calls without actually executing them:

```bash
ferry-cli -w cloneResource --clone=orig --new_resource=new -u --dryrun
```

### Server Override

Use a different server than configured:

```bash
ferry-cli -e getUserInfo --username=username --server=https://dev.hostname.domain:1234/
```

### Update Swagger File

Get the latest API specification:

```bash
ferry-cli -u
```

### Show Configuration

```bash
# Locate and print configuration file path
ferry-cli --show-config-file
```

### Show Version

```bash
ferry-cli --version
```

---

## Examples by Use Case

### User Management

```bash
# Get user information
ferry-cli -e getUserInfo --username=johndoe

# List all users
ferry-cli -e getAllUsers

# Add user to group
ferry-cli -e addUserToGroup --username=johndoe --groupname=mygroup --grouptype=UnixGroup

# Remove user from group
ferry-cli -e removeUserFromGroup --username=johndoe --groupname=mygroup --grouptype=UnixGroup
```

### Group Management

```bash
# Get all groups
ferry-cli -e getAllGroups

# Get groups for a user
ferry-cli -e getUserGroups --username=johndoe

# Get group members
ferry-cli -e getGroupMembers --groupname=mygroup
```

### Resource Management

```bash
# List all compute resources
ferry-cli -e getAllComputeResources

# Get user access to resources
ferry-cli -e getUserAccessToComputeResource --username=johndoe

# Set user access to resource
ferry-cli -e setUserAccessToComputeResource --username=johndoe --resourcename=resource_name --unitname=unit_name
```

### Chaining Responses with jq

Ferry CLI returns JSON responses whose `ferry_output` field can be chained through `jq` for shell scripting:

```bash
# Extract ferry_output from response
ferry-cli -e getUserInfo --username=johndoe | jq '.ferry_output'

# Get specific field from output
ferry-cli -e getUserInfo --username=johndoe | jq '.ferry_output.fullname'

# List all groups and filter by name
ferry-cli -e getAllGroups | jq '.ferry_output[] | select(.groupname | contains("mygroup"))'

# Extract usernames from a list of users
ferry-cli -e getAllUsers | jq '.ferry_output[].username'
```
---

## Notes

- **Endpoint naming**: Endpoints can be specified in snake_case, kebab-case, or camelCase - the CLI will automatically normalize them.
- **Leading underscores**: If an endpoint starts with an underscore, preserve it by using `--endpoint _myEndpoint`.
- **Response format**: All responses include `ferry_status`, `ferry_error`, and `ferry_output` fields. 

