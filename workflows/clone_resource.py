from ferry import FerryApi, get_default_cert_path, get_default_capath
from argparse import Namespace, ArgumentParser
import json

cert = get_default_cert_path()
capath = get_default_capath()
# TODO: This is incomplete and should be reviewed
parser = ArgumentParser(description="Custom Ferry sequence to clone a resource")
parser.add_argument('--cert', required=(cert is None), default=cert, help="Path to cert")
parser.add_argument('--capath', required=(capath is None), default=capath, help="Certificate authority path")
parser.add_argument('-r', '--resource', required=True, help="Resource to be cloned")
parser.add_argument('-n', '--new_resource', help="Name of new resource")
parser.add_argument('-u', '--unitname', help="Affiliation the role belongs to")


ferry_api = FerryApi()
args = parser.parse_args()

resp = eval(ferry_api.execute_endpoint("getGroupAccessToResource", [f"--resource={args.resource}", f"--unitname={args.unitname}"]))
groups = resp.get("ferry_output")
group_users = []
for group in groups:
    resp = json.loads(ferry_api.execute_endpoint("getUserGroupsForComputeResource", [f"--unitname={group}"])).get("ferry_output",None)
    group_users.extend([resource_group for resource_group in resp if resource_group["resourcename"] == f"{args.resource}"])
print(group_users)

