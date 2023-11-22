

def GetGroupInfo(api, params):
    group_json = api.call_endpoint("getAllGroups")
    if not group_json:
        print(f"Failed'")
        exit(1)
    print(f"Recieved successful response'")
    print(f"Filtering by groupname: '{params['groupname']}'")
    group_info = [entry for entry in group_json["ferry_output"] if entry["groupname"] == params["groupname"]]
    return group_info
