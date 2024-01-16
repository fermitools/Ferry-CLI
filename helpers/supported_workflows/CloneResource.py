import sys
from typing import Any

from helpers.api import FerryAPI
from helpers.workflows import Workflow


class CloneResource(Workflow):
    def __init__(self: "CloneResource") -> None:
        self.name = "cloneResource"
        self.method = "PUT"
        self.description = "Clones an existing resource. Maintaining the same group and user access as the original resource."
        self.params = [
            {
                "name": "clone",
                "description": "Resource to be cloned",
                "type": "string",
                "required": True,
            },
            {
                "name": "new_resource",
                "description": "Name of new resource",
                "type": "string",
                "required": True,
            },
            {
                "name": "unitname",
                "description": "Affiliation the resource belongs to",
                "type": "string",
                "required": True,
            },
        ]
        super().__init__()

    def run(self: "CloneResource", api: "FerryAPI", args: Any) -> Any:  # type: ignore
        # Get all compute resources and filter out the resource to be cloned, and the cloned resource - if it already exists
        try:
            resources = {
                resource["resourcename"]: resource
                for resource in self.verify_output(
                    api.call_endpoint("getAllComputeResources")
                )
                if resource.get("resourcename", "")
                in [args["clone"], args["new_resource"]]
            }
            print(resources)
            # Verify that resource to be cloned exists
            if args["clone"] not in resources:
                raise ValueError("Resource to be cloned does not exist")

            # If the clone doesnt exist, create a resource with the same details, just changing the provided name
            cloned_resource_data = dict(resources[args["clone"]])
            cloned_resource_data["resourcename"] = args["new_resource"]
            print(cloned_resource_data)
            if args["new_resource"] not in resources:
                print(
                    f"New resource doesn't exist. Creating new resource with the same attributes as: {args['clone']}"
                )
                self.verify_output(
                    api.call_endpoint(
                        "createComputeResource",
                        method="PUT",
                        params=cloned_resource_data,
                    )
                )
            else:
                # If the clone already exists, we will update its info
                self.verify_output(
                    api.call_endpoint(
                        "setComputeResourceInfo",
                        method="POST",
                        params=cloned_resource_data,
                    )
                )

            # Now we will get all user groups, and filter for the original resource
            group_json = self.verify_output(
                api.call_endpoint(
                    "getUserGroupsForComputeResource",
                    method="GET",
                    params={"unitname": args["unitname"]},
                )
            )
            print(f"Received response, searching for resource: {args['clone']}")
            resources = [resource for resource in group_json if resource.get("resourcename", "") == args["clone"]]  # type: ignore
            if resources:
                # Add each user from the original resource into the new resource with the same configurations
                for resource in resources:
                    print(f"Found Resources")
                    print(resource)
                    for user in resource.get("users", []):
                        user_access_data = dict(user)
                        user_access_data["resourcename"] = args["new_resource"]
                        print(
                            f"Updating user access to {args['new_resource']} for {user['username']}"
                        )
                        if "status" in user_access_data:
                            del user_access_data["status"]
                        self.verify_output(
                            api.call_endpoint(
                                "setUserAccessToComputeResource",
                                method="PUT",
                                params=user_access_data,
                            )
                        )

            print(
                f"Resource '{args['clone']}' has been successful cloned as '{args['new_resource']}'"
            )
            sys.exit(0)
        except Exception as e:
            raise e

    def verify_output(self: "CloneResource", response: Any) -> Any:
        if not response:
            print("Failed'")
            sys.exit(1)
        if "ferry_status" in response and response.get("ferry_status", "") != "success":
            print(f"{response}")
            sys.exit(1)
        return response["ferry_output"]
