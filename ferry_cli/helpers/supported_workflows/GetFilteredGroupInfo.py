# pylint: disable=invalid-name,arguments-differ
from typing import Any, Dict, List

try:
    from ferry_cli.helpers.workflows import Workflow
except ImportError:
    from helpers.workflows import Workflow  # type: ignore


class GetFilteredGroupInfo(Workflow):
    def __init__(self: "GetFilteredGroupInfo") -> None:
        self.name: str = "getFilteredGroupInfo"
        self.method: str = "GET"
        self.description: str = "Returns gid, groupname, and grouptype for all groups with 'groupname' variable in its name."
        self.params: List[Dict[str, Any]] = [
            {
                "name": "groupname",
                "description": "Name of the group",
                "type": "string",
                "required": True,
            }
        ]
        super().__init__()

    def run(self, api, args):  # type: ignore # pylint: disable=arguments-differ
        group_json = self.verify_output(api, api.call_endpoint("getAllGroups"))
        if api.dryrun:
            return []
        if not api.quiet:
            print("Received successful response")
            print(f"Filtering by groupname: '{args['groupname']}'")
        group_info = [
            entry for entry in group_json if entry["groupname"] == args["groupname"]
        ]
        return group_info
