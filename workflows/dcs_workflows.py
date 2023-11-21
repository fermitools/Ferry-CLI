import json


def validate_args(required_params, optional_params, args):
    pass

class Workflow:
    def __init__(self, ferry_api):
        self.ferry_api = ferry_api
        self.existing_workflows = {"getAllGroups": GetGroupInfo}
        
        

class GetGroupInfo:
    def __init__(self):
         # Params: {Name: Type}
        self.optional_params = {}
        self.required_params = {"groupname": type(str())}
         # What does the workflow do?
        self.description = "Returns gid, groupname, and grouptype for all groups with 'groupname' variable in its name."

    def run(self):
        url, group_json = self.api.generate_request("getAllGroups")
        group_info = [entry for entry in group_json["ferry_output"] if entry["groupname"] == self.groupname]
        if group_info and not self.api.quiet:
            print(json.dumps(group_info, indent=4))
            print()
        self.response = group_info
    