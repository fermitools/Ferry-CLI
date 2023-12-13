class SafeguardsDCS:
    def __init__(self) -> None:
        # TODO: Add more as needed
        # Format as: {"Endpoint": function (without brackets) }
        self.endpoint_safeguards = {"createUser": self.createUser}

    # Checks "endpoint_safeguards" dictionary to see if endpoint is safeguarded
    # Calls the associated function
    def verify(self, endpoint: str) -> None:
        if endpoint in self.endpoint_safeguards:
            self.endpoint_safeguards[endpoint]()
            # Prevent the program from continuing
            exit(1)

    # Below are the functions to run for information related to safeguarded endpoints.
    # Rather than calling the endpoint, we will print out the proper steps to take, forms to fill out, etc..
    def createUser(self) -> None:
        print(
            """
              SAFEGUARDED: DCS Should NOT be using this call.

              Use this form to get a UID/GID if needed: https://fermi.servicenowservices.com/wp?id=evg_sc_cat_item&sys_id=97be09036f276d005232ce026e3ee435
              Then do whatever you needed to do.
              """
        )
