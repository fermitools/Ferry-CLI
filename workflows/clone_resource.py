from argparse import Namespace, ArgumentParser
import json

from helpers.api import FerryAPI
from helpers.auth import *


cert = get_default_cert_path()
capath = DEFAULT_CA_DIR
base_url = "https://ferry.fnal.gov:8445/"  # TODO This was just put in there to make the mypy tests pass.  LTrestka is currently working on a large refactor of workflows

# TODO: This is incomplete and should be reviewed
parser = ArgumentParser(description="Custom Ferry sequence to clone a resource")
parser.add_argument(
    "--cert", required=(cert is None), default=cert, help="Path to cert"
)
parser.add_argument(
    "--capath",
    required=(capath is None),
    default=capath,
    help="Certificate authority path",
)
parser.add_argument("-r", "--resource", required=True, help="Resource to be cloned")
parser.add_argument("-n", "--new_resource", help="Name of new resource")
parser.add_argument("-u", "--unitname", help="Affiliation the role belongs to")


ferry_api = FerryAPI(base_url=base_url)
args = parser.parse_args()

# This is type-ignored, since LTrestka plans on refactoring this anyway
resp = eval(
    ferry_api.call_endpoint(
        "getGroupAccessToResource",
        [f"--resource={args.resource}", f"--unitname={args.unitname}"],  # type: ignore
    )
)
groups = resp.get("ferry_output")
group_users = []
# This is type-ignored, since LTrestka plans on refactoring this anyway
for group in groups:
    resp = json.loads(
        ferry_api.call_endpoint(
            "getUserGroupsForComputeResource", [f"--unitname={group}"]  # type: ignore
        )
    ).get("ferry_output", None)
    group_users.extend(
        [
            resource_group
            for resource_group in resp
            if resource_group["resourcename"] == f"{args.resource}"
        ]
    )
print(group_users)
