import json
from typing import Dict, Any, Type


def validate_args(
    required_params: Dict[str, Any], optional_params: Dict[str, Any], args: Any
) -> None:
    pass


class Workflow:
    def __init__(self, ferry_api: Type[object]) -> None:
        self.ferry_api = ferry_api
        self.existing_workflows = {"getAllGroups": GetGroupInfo}


class GetGroupInfo:
    def __init__(self) -> None:
        # Params: {Name: Type}
        self.optional_params: Dict[str, Any] = {}
        self.required_params: Dict[str, Any] = {"groupname": type(str())}
        # What does the workflow do?
        self.description = "Returns gid, groupname, and grouptype for all groups with 'groupname' variable in its name."

    def run(self) -> None:
        url, group_json = self.api.generate_request("getAllGroups")  # type: ignore
        group_info = [
            entry
            for entry in group_json["ferry_output"]
            if entry["groupname"] == self.groupname  # type: ignore
        ]
        if group_info and not self.api.quiet:  # type: ignore
            print(json.dumps(group_info, indent=4))
            print()
        self.response = group_info
