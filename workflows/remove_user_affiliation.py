

from ferry import FerryApi, get_default_cert_path, get_default_capath
from argparse import Namespace, ArgumentParser
import json

cert = get_default_cert_path()
capath = get_default_capath()

parser = ArgumentParser(description="Custom Ferry sequence to clone a resource")
parser.add_argument('--cert', required=(cert is None), default=cert, help="Path to cert")
parser.add_argument('--capath', required=(capath is None), default=capath, help="Certificate authority path")
parser.add_argument('-r', '--resource', required=True, help="Resource to be cloned")
parser.add_argument('-n', '--new_resource', help="Name of new resource")
parser.add_argument('--unitname', help="Affiliation the role belongs to")
parser.add_argument('--username', help="Affiliation the role belongs to")
ferry_api = FerryApi()
args = parser.parse_args()



resp = eval(ferry_api.execute_endpoint("getUserAccessToComputeResources", [f"--username={args.username}"]))
resources = resp.get("ferry_output")

for resource in resources:
    if args.unitname in resource.get("resourcename") or args.unitname in resource.get("groupname"):
        resp = json.loads(
            ferry_api.execute_endpoint("removeUserFromComputeResource",
                                       [f"--resourcename={resource.get('resourcename')}",
                                        f"--resourcetype={resource.get('resourcetype')}",
                                        f"--username={args.username}",
                                        f"--groupname={resource.get('groupname')}"
                                        ])).get("ferry_output",None)


user_fqans = eval(ferry_api.execute_endpoint("getUserFQANs",[f"--unitname={args.unitname}",f"--username={args.username}"])).get("ferry_output")
for item in user_fqans:
        ferry_api.execute_endpoint("removeUserExperimentFQAN",[f"--unitname={args.unitname}",f"--username={args.username}", f"--fqan={item.get('fqan')}"])
        
user_groups = eval(ferry_api.execute_endpoint("getUserGroups",[f"--username={username}"])).get("ferry_output")
for item in user_groups:
    if unitname in item.get("groupname"):
        ferry_api.execute_endpoint("removeUserFromGroup",[f"--groupname={item.get('groupname')}",f"--username={username}", f"--grouptype={item.get('grouptype')}"])

ferry_api.execute_endpoint("/setUserGridAccess",[f"--unitname={unitname}",f"--username={username}"])

cert_dns = eval(ferry_api.execute_endpoint("getUserCertificateDNs",[f"--unitname={unitname}",f"--username={username}"])).get("ferry_output")
for certs in cert_dns:
    for cert in certs.get("certificates", []):
        print(cert)
        

        

