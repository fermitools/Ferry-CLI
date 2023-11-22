from ferry import FerryApi, get_default_cert_path, get_default_capath
from argparse import Namespace, ArgumentParser
import json


cert = get_default_cert_path()
capath = get_default_capath()

parser = ArgumentParser(
    description="Custom Ferry function to create, and add a group to a unit, and add resources to it"
)
parser.add_argument(
    "--cert", required=(cert is None), default=cert, help="Path to cert"
)
parser.add_argument(
    "--capath",
    required=(capath is None),
    default=capath,
    help="Certificate authority path",
)
parser.add_argument("-c", "--create_group", help="Create the group", default=False)
parser.add_argument("-g", "--groupname", help="Resource to be cloned")
parser.add_argument(
    "-p",
    "--primary",
    help="True if this is the primary group for the affiliation - default(false)",
    default=False,
)
parser.add_argument(
    "-r",
    "--resources",
    nargs="*",
    help="Resources to be added to (getPasswdFile)",
    default=None,
)
parser.add_argument("-u", "--unitname", help="Affiliation to associate the group with")
ferry_api = FerryApi()
args = parser.parse_args()

# TODO: This is incomplete
if args.resources is not None:
    print("\nArguments: ")
    for key, val in vars(args).items():
        print(f"\t{key}: {val}")
    for resource in args.resources:
        resp = eval(
            ferry_api.execute_endpoint(
                "getPasswdFile",
                [
                    f"--groupname={args.groupname}",
                    f"--unitname={args.unitname}",
                    f"--resourcename={resource}",
                ],
            )
        )
        output = resp.get("ferry_output", None) if resp else None
        if output and args.unitname in output:
            if (
                "resources" in output[args.unitname]
                and resource in output[args.unitname]["resources"]
            ):
                for user in output[args.unitname]["resources"][resource]:
                    resp = json.loads(
                        ferry_api.execute_endpoint(
                            "setUserAccessToComputeResource",
                            [
                                f"--groupname={args.groupname}",
                                f"--homedir={user.get('homedir', None)}",
                                f"--resourcename={resource}",
                                f"--primary={args.primary}",
                                f"--shell={user.get('shell', None)}",
                                f"--username={user.get('username', None)}",
                            ],
                        )
                    )
                    if (
                        resp
                        and "ferry_status" in resp
                        and resp["ferry_status"] == "success"
                    ):
                        print(
                            f"Added User {user.get('username', '')} to resource: {resource}"
                        )


else:
    parser.print_help()
