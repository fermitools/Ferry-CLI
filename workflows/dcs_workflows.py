import json

class GetGroupInfo:
    def __init__(self, ferry_api, group):
        self.api = ferry_api
        self.optional_params = {}
        self.required_params = {"groupname": "string"}
        self.groupname = group
        self.response=None
        self.run()

    def run(self):
        url, group_json = self.api.generate_request("getAllGroups")
        group_info = [entry for entry in group_json["ferry_output"] if entry["groupname"] == self.groupname]
        if group_info and not self.api.quiet:
            print(json.dumps(group_info, indent=4))
            print()
        self.response = group_info
    