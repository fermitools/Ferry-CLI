from argparse import Namespace, ArgumentParser
import json

from helpers.api import FerryAPI
from helpers.auth import *


cert = get_default_cert_path()
capath = DEFAULT_CA_DIR
base_url = "https://ferry.fnal.gov:8445/"  # TODO This was just put in there to make the mypy tests pass.  LTrestka is currently working on a large refactor of workflows

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
parser.add_argument("--unitname", help="Affiliation the role belongs to")
parser.add_argument("--username", help="Affiliation the role belongs to")
ferry_api = FerryAPI(base_url=base_url)
args = parser.parse_args()


# This is type-ignored, since LTrestka plans on refactoring this anyway
resp = eval(
    ferry_api.call_endpoint(
        "getUserAccessToComputeResources", [f"--username={args.username}"]  # type: ignore
    )
)
resources = resp.get("ferry_output")

for resource in resources:
    if args.unitname in resource.get("resourcename") or args.unitname in resource.get(
        "groupname"
    ):
        resp = json.loads(
            # This is type-ignored, since LTrestka plans on refactoring this anyway
            ferry_api.call_endpoint(
                "removeUserFromComputeResource",
                [  # type: ignore
                    f"--resourcename={resource.get('resourcename')}",
                    f"--resourcetype={resource.get('resourcetype')}",
                    f"--username={args.username}",
                    f"--groupname={resource.get('groupname')}",
                ],
            )
        ).get("ferry_output", None)

        # This is type-ignored, since LTrestka plans on refactoring this anyway
user_fqans = eval(
    ferry_api.call_endpoint(
        "getUserFQANs", [f"--unitname={args.unitname}", f"--username={args.username}"]  # type: ignore
    )
).get("ferry_output")
# This is type-ignored, since LTrestka plans on refactoring this anyway
for item in user_fqans:
    ferry_api.call_endpoint(
        "removeUserExperimentFQAN",
        [  # type: ignore
            f"--unitname={args.unitname}",
            f"--username={args.username}",
            f"--fqan={item.get('fqan')}",
        ],
    )

    # This is type-ignored, since LTrestka plans on refactoring this anyway
user_groups = eval(
    ferry_api.call_endpoint("getUserGroups", [f"--username={args.username}"])  # type: ignore
).get("ferry_output")
for item in user_groups:
    if args.unitname in item.get("groupname"):
        # This is type-ignored, since LTrestka plans on refactoring this anyway
        ferry_api.call_endpoint(
            "removeUserFromGroup",
            [  # type: ignore
                f"--groupname={item.get('groupname')}",
                f"--username={args.username}",
                f"--grouptype={item.get('grouptype')}",
            ],
        )

        # This is type-ignored, since LTrestka plans on refactoring this anyway
ferry_api.call_endpoint(
    "/setUserGridAccess", [f"--unitname={args.unitname}", f"--username={args.username}"]  # type: ignore
)

# This is type-ignored, since LTrestka plans on refactoring this anyway
cert_dns = eval(
    ferry_api.call_endpoint(
        "getUserCertificateDNs",
        [f"--unitname={args.unitname}", f"--username={args.username}"],  # type: ignore
    )
).get("ferry_output")
for certs in cert_dns:
    for cert in certs.get("certificates", []):
        print(cert)
