from argparse import Namespace, ArgumentParser
import json

from helpers.api import FerryAPI
from helpers.workflows import Workflow

#TODO: ask about thought process behind abstract workflow class and why we pass in as parameter vs a static member for whole Workflow class
class SetUserAccessToComputeResource(Workflow):
    def __init__(self: "SetUserAccessToComputeResource") -> None:
        self.name = "setUserAccessToComputeResource"
        self.method = "PUT"
        self.description = "The LQCD version of addUserToExperiment"
        #TODO: Ask about if there should be a params like this for each header in the request?
        self.params = [
            {
                "name": "groupname",
                ""
            }
        ]
        super().__init__()
        #TODO: ask about use of super here to understand inheritance

    #TODO ask about this signature, is api a FerrayAPI object? Assuming args is from arg parser
    def run(self, api, args):
        #TODO: not sure how to proceed from here looking at getFilteredGroupInfo example isn't quite relevant to what we do here

# cert = get_default_cert_path()
# capath = DEFAULT_CA_DIR
# base_url = "https://ferry.fnal.gov:8445/"  # TODO This was just put in there to make the mypy tests pass.  LTrestka is currently working on a large refactor of workflows

# parser = ArgumentParser(
#     description="The LQCD version of addUserToExperiment"
# )

# parser.add_argument(
# "--cert", required=(cert is None), default=cert, help="Path to x509 proxy"
#     #TODO: have lucas explain the precise logical flow of above
# )

# parser.add_argument("--key", required=True, default=cert, help="should be same as path to x509 proxy")

# #TODO: after confirming that this can use token worflow, add that option

# parser.add_argument("-r", "--resourceName", help="for LQCD this should by default be lqcd_cluster", default="lqcd_cluster", required=True)
# #TODO: ask what the behaviour is if something is both required and default but is omitted? Superflous to have both?
# parser.add_argument("-p", "--primary", help="set true or false if this will be the users primary affiliation", default=False)
# parser.add_argument("-u", "--user", help="the user to be added", required=True)
# parser.add_argument("-h", "--homedir", help="specify optional special home directory path", default="/home/" + USERNAMEFROMARGSABOVE)
# parser.add_argument("-g", "--groupname", help="Experiment to be added to", required=True)

# # Do we need to have an of args.whatever is not None contingency here, if these are marked as required and they are empty what happens?

# #TODO: when I looked at the rest of the file I saw the todo about it being "incomplete",
# # going to wait for guidance from Lucas on what the rest of the process should actually contain or if I should leave beyond here to him
