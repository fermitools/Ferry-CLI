# pylint: disable=invalid-name,arguments-differ,unused-import
import sys
from typing import Any, List

try:
    from ferry_cli.helpers.api import FerryAPI
    from ferry_cli.helpers.auth import DebugLevel
    from ferry_cli.helpers.workflows import Workflow
except ImportError:
    from helpers.api import FerryAPI  # type: ignore
    from helpers.auth import DebugLevel  # type: ignore
    from helpers.workflows import Workflow  # type: ignore


class NewCapabilitySet(Workflow):
    def __init__(self: "NewCapabilitySet") -> None:
        self.name = "newCapabilitySet"
        self.method = "PUT"
        self.description = (
            "Creates a new capability set based on a given role and unix group"
        )
        self.params = [
            {
                "name": "groupname",
                "description": "UNIX group the new capability set will be associated with",
                "type": "string",
                "required": True,
            },
            {
                "name": "gid",
                "description": "GID of the UNIX group groupname",
                "type": int,
                "required": True,
            },
            {
                "name": "unitname",
                "description": "Affiliation Unit the new capability set will be associated with",
                "type": "string",
                "required": True,
            },
            {
                "name": "fqan",
                "description": "FQAN associated with the new capability set",
                "type": "string",
                "required": True,
            },
            {
                "name": "setname",
                "description": "Name of the new capability set",
                "type": "string",
                "required": True,
            },
            {
                "name": "scopes_pattern",
                "description": "Scopes of the new capability set",
                "type": "string",
                "required": True,
            },
            {
                "name": "mapped_user",
                "description": "If the capability set needs to be mapped to a specific user, this is that mapped username",
                "type": "string",
                "required": False,
            },
            {
                "name": "token_subject",
                "description": (
                    "The default will just be setname@fnal.gov, but if the resultant token should have the user UID from FERRY as the subject "
                    + 'then set this to the string "none"'
                ),
                "type": "string",
                "required": False,
            },
            {
                "name": "vault_storage_key",
                "description": (
                    'The default will just be setname, but if the intent is to not store this vault storage key in LDAP, set this to the string "none"'
                ),
                "type": "string",
                "required": False,
            },
        ]
        super().__init__()

    def run(self: "NewCapabilitySet", api: "FerryAPI", args: Any) -> Any:  # type: ignore # pylint: disable=arguments-differ,too-many-branches,too-many-statements
        """Run the workflow to add a new capability set to FERRY"""
        if api.dryrun:
            print(
                "WARNING:  This workflow is being run with the --dryrun flag.  The exact steps shown here may differ since "
                "some of the workflow steps depend on the output of API calls."
            )

        # Note - we don't have explicit dryrun checks here because the FerryAPI class handles that for us
        # 1. Create new group in FERRY
        try:
            self.verify_output(
                api,
                api.call_endpoint(
                    "createGroup",
                    method="PUT",
                    params={
                        "groupname": args["groupname"],
                        "gid": args["gid"],
                        "grouptype": "UnixGroup",
                    },
                ),
            )
        except Exception as e:  # pylint: disable=broad-except
            if api.debug_level != DebugLevel.QUIET:
                print("Failed to create group")
            if "groupname already exists" in str(e):
                print(
                    f"Group {args['groupname']} already exists in FERRY.  Continuing with the workflow."
                )
            else:
                raise

        # Check
        if not api.dryrun:
            try:
                response = self.verify_output(
                    api,
                    api.call_endpoint(
                        "getGroupName",
                        params={"gid": args["gid"]},
                    ),
                )
                if response["groupname"] != args["groupname"]:
                    print(
                        f"Group name {response['groupname']} does not match expected group name {args['groupname']}"
                    )
                    raise ValueError("Group name mismatch")
            except Exception:  # pylint: disable=broad-except
                if api.debug_level != DebugLevel.QUIET:
                    print("Failed to verify group creation")
                raise

        # 2. Add group to unit
        try:
            self.verify_output(
                api,
                api.call_endpoint(
                    "addGroupToUnit",
                    method="PUT",
                    params={
                        "groupname": args["groupname"],
                        "unitname": args["unitname"],
                        "grouptype": "UnixGroup",
                    },
                ),
            )
        except Exception:  # pylint: disable=broad-except
            if api.debug_level != DebugLevel.QUIET:
                print("Failed to add group to unit")
            raise

        # Check
        if not api.dryrun:
            try:
                response = self.verify_output(
                    api,
                    api.call_endpoint(
                        "getGroupUnits",
                        params={"groupname": args["groupname"]},
                    ),
                )
                units = (entry["unitname"] for entry in response)
                for unit in units:
                    if unit == args["unitname"]:
                        break
                else:
                    raise ValueError(
                        f"Group {args['groupname']} does not belong to unit {args['unitname']}"
                    )
            except Exception:  # pylint: disable=broad-except
                if api.debug_level != DebugLevel.QUIET:
                    print("Failed to verify group-unit association")
                raise

        # TODO Test this case # pylint: disable=fixme
        # 2a. Optional - add mapped user to group
        if args.get("mapped_user", ""):
            try:
                self.verify_output(
                    api,
                    api.call_endpoint(
                        "addUserToGroup",
                        method="PUT",
                        params={
                            "groupname": args["groupname"],
                            "username": args["mapped_user"],
                            "grouptype": "UnixGroup",
                        },
                    ),
                )
            except Exception:
                if api.debug_level != DebugLevel.QUIET:
                    print("Failed to add mapped user to group")
                raise
            # Check
            if not api.dryrun:
                try:
                    response = self.verify_output(
                        api,
                        api.call_endpoint(
                            "getGroupMembers",
                            params={"groupname": args["groupname"]},
                        ),
                    )
                    users = (entry["username"] for entry in response)
                    for user in users:
                        if user == args["mapped_user"]:
                            break
                    else:
                        raise ValueError(
                            f"Mapped user {args['mapped_user']} does not belong to group {args['groupname']}"
                        )
                except Exception:
                    if api.debug_level != DebugLevel.QUIET:
                        print("Failed to verify mapped user-group association")
                    raise

        # 3. Create new FQAN
        try:
            params = {
                "fqan": args["fqan"],
                "unitname": args["unitname"],
                "groupname": args["groupname"],
            }
            if args.get("mapped_user"):
                params["username"] = args["mapped_user"]

            self.verify_output(
                api,
                api.call_endpoint(
                    "createFQAN",
                    method="PUT",
                    params=params,
                ),
            )
        except Exception:  # pylint: disable=broad-except
            if api.debug_level != DebugLevel.QUIET:
                print("Failed to create FQAN")
            raise

        # No Check available for FQAN creation at this time

        # 4. Create capability set
        try:
            new_cap_set_params = {
                "setname": args["setname"],
                "pattern": args["scopes_pattern"],
            }
            if args.get("token_subject", None) is not None:
                new_cap_set_params["tokensubject"] = args["token_subject"]
            if args.get("vault_storage_key", None) is not None:
                new_cap_set_params["vaultstoragekey"] = args["vault_storage_key"]

            self.verify_output(
                api,
                api.call_endpoint(
                    "createCapabilitySet",
                    method="PUT",
                    params=new_cap_set_params,
                ),
            )
        except Exception:  # pylint: disable=broad-except
            if api.debug_level != DebugLevel.QUIET:
                print("Failed to create capability set")
            raise
        # Check will be after next step

        # 5. Associate capability set with FQAN
        role = self._calculate_role(args["fqan"])
        if not role:
            print(f"Failed to calculate role from FQAN {args['fqan']}")
            raise ValueError("Role calculation failed")
        try:
            self.verify_output(
                api,
                api.call_endpoint(
                    "addCapabilitySetToFQAN",
                    method="PUT",
                    params={
                        "setname": args["setname"],
                        "unitname": args["unitname"],
                        "role": role,
                    },
                ),
            )
        except Exception:  # pylint: disable=broad-except
            if api.debug_level != DebugLevel.QUIET:
                print("Failed to associate capability set with FQAN")
            raise

        # Check all capability set settings
        if not api.dryrun:
            try:
                response = self.verify_output(
                    api,
                    api.call_endpoint(
                        "getCapabilitySet",
                        params={"setname": args["setname"]},
                    ),
                )
                # For some reason, the getCapabilitySet API returns a list, so we need to extract the first element
                set_info = response[0]

                # Verify that the capability set name matches the expected name
                try:
                    assert set_info["setname"] == args["setname"]
                except AssertionError:
                    raise ValueError(
                        f"Capability set name {set_info['setname']} does not match expected name {args['setname']}"
                    )

                # Verify that the capability set pattern matches the expected pattern
                try:
                    assert self._check_lists_for_same_elts(
                        set_info["patterns"],
                        self.scopes_string_to_list(args["scopes_pattern"]),
                    )
                except AssertionError:
                    raise ValueError(
                        f"Capability set pattern {set_info['patterns']} does not match expected pattern {args['scopes_pattern']}"
                    )

                # Verify that the capability set FQAN and role matches the expected FQAN and role
                role_entries = (entry for entry in set_info["roles"])
                for entry in role_entries:
                    if entry["role"] == role:
                        try:
                            assert entry["fqan"] == args["fqan"]
                        except AssertionError:
                            raise ValueError(
                                f"Capability set role {entry['role']} does not match expected role {role}"
                            )
                        break  # Good case - role and fqan match
                else:
                    raise ValueError(
                        f"Capability set role does not match expected role {role} or FQAN {args['fqan']} is not found in proper role entry"
                    )
            except Exception:  # pylint: disable=broad-except
                if api.debug_level != DebugLevel.QUIET:
                    print("Failed to verify capability set creation")
                raise
        print(f"Successfully created capability set {args['setname']}.")

    @staticmethod
    def scopes_string_to_list(
        scopes_string: str, out_delimiter: str = ","
    ) -> List[str]:
        """Convert a scopes string to a list of scopes delimited by out_delimiter
        e.g. "scope1,scope2" -> ["scope1", "scope2"]
        """
        if not scopes_string:
            return []
        return scopes_string.split(out_delimiter)

    @staticmethod
    def _check_lists_for_same_elts(list1: List[str], list2: List[str]) -> bool:
        """Compare two lists for the same elements, regardless of order"""
        return sorted(list1) == sorted(list2)

    @staticmethod
    def _calculate_role(fqan: str) -> str:
        """Calculate the role from the FQAN
        Something like /fermilab/Role=Rolename/Capability=NULL -> Rolename
        """
        parts = fqan.split("/")
        for part in parts:
            if part.startswith("Role="):
                return part.split("=")[1]
        return ""
