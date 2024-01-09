# pylint: disable=invalid-name
import sys

from typing import Any




from helpers.workflows import Workflow


class GetFilteredGroupInfo(Workflow):
    def __init__(self: "GetFilteredGroupInfo") -> None:
        self.name = "getFilteredGroupInfo"
        self.method = "GET"
        self.description = "Returns gid, groupname, and grouptype for all groups with 'groupname' variable in its name."
        self.params = [
            {
                "name": "groupname",
                "description": "Name of the group",
                "type": "string",
                "required": True,
            }
        ]
        super().__init__()

    def run(self, api, args):  # type: ignore #pylint: disable=arguments-differ
        group_json = api.call_endpoint("getAllGroups")
        if not group_json:
            print("Failed'")
            sys.exit(1)
        print("Received successful response")
        print(f"Filtering by groupname: '{args['groupname']}'")
        group_info = [
            entry
            for entry in group_json["ferry_output"]
            if entry["groupname"] == args["groupname"]
        ]
        return group_info
