import pytest

from ferry_cli.helpers.api import FerryAPI
from ferry_cli.helpers.auth import Auth
from ferry_cli.helpers.supported_workflows.NewCapabilitySet import NewCapabilitySet


@pytest.mark.parametrize(
    "args, expected",
    [
        (
            {
                "groupname": "testgroup",
                "gid": 1234,
                "unitname": "testunit",
                "fqan": "/org/Role=myrole/Capability=NULL",
                "setname": "testcapabilityset",
                "scopes_pattern": "scope1,scope2",
            },
            [
                (
                    "Would call endpoint: https://example.com/createGroup with params\n"
                    + "{'groupname': 'testgroup', 'gid': 1234, 'grouptype': 'UnixGroup'}"
                ),
                (
                    "Would call endpoint: https://example.com/addGroupToUnit with params\n"
                    + "{'groupname': 'testgroup', 'unitname': 'testunit', 'grouptype': 'UnixGroup'}"
                ),
                (
                    f"Would call endpoint: https://example.com/createFQAN with params\n"
                    + "{'fqan': '/org/Role=myrole/Capability=NULL', 'unitname': 'testunit', 'groupname': 'testgroup'}"
                ),
                (
                    "Would call endpoint: https://example.com/createCapabilitySet with params\n"
                    + "{'setname': 'testcapabilityset', 'pattern': 'scope1,scope2'}"
                ),
                (
                    "Would call endpoint: https://example.com/addCapabilitySetToFQAN with params\n"
                    + "{'setname': 'testcapabilityset', 'unitname': 'testunit', 'role': 'myrole'}"
                ),
            ],
        ),
        (
            {
                "groupname": "testgroup",
                "gid": 1234,
                "unitname": "testunit",
                "fqan": "/org/Role=myrole/Capability=NULL",
                "setname": "testcapabilityset",
                "scopes_pattern": "scope1,scope2",
                "token_subject": "none",
            },
            [
                (
                    "Would call endpoint: https://example.com/createGroup with params\n"
                    + "{'groupname': 'testgroup', 'gid': 1234, 'grouptype': 'UnixGroup'}"
                ),
                (
                    "Would call endpoint: https://example.com/addGroupToUnit with params\n"
                    + "{'groupname': 'testgroup', 'unitname': 'testunit', 'grouptype': 'UnixGroup'}"
                ),
                (
                    f"Would call endpoint: https://example.com/createFQAN with params\n"
                    + "{'fqan': '/org/Role=myrole/Capability=NULL', 'unitname': 'testunit', 'groupname': 'testgroup'}"
                ),
                (
                    "Would call endpoint: https://example.com/createCapabilitySet with params\n"
                    + "{'setname': 'testcapabilityset', 'pattern': 'scope1,scope2', 'token_subject': 'none'}"
                ),
                (
                    "Would call endpoint: https://example.com/addCapabilitySetToFQAN with params\n"
                    + "{'setname': 'testcapabilityset', 'unitname': 'testunit', 'role': 'myrole'}"
                ),
            ],
        ),
        (
            {
                "groupname": "testgroup",
                "mapped_user": "testuser",
                "gid": 1234,
                "unitname": "testunit",
                "fqan": "/org/Role=myrole/Capability=NULL",
                "setname": "testcapabilityset",
                "scopes_pattern": "scope1,scope2",
            },
            [
                (
                    "Would call endpoint: https://example.com/createGroup with params\n"
                    + "{'groupname': 'testgroup', 'gid': 1234, 'grouptype': 'UnixGroup'}"
                ),
                (
                    "Would call endpoint: https://example.com/addGroupToUnit with params\n"
                    + "{'groupname': 'testgroup', 'unitname': 'testunit', 'grouptype': 'UnixGroup'}"
                ),
                (
                    "Would call endpoint: https://example.com/addUserToGroup with params\n"
                    + "{'groupname': 'testgroup', 'username': 'testuser', 'grouptype': 'UnixGroup'}"
                ),
                (
                    f"Would call endpoint: https://example.com/createFQAN with params\n"
                    + "{'fqan': '/org/Role=myrole/Capability=NULL', 'unitname': 'testunit', 'groupname': 'testgroup', 'username': 'testuser'}"
                ),
                (
                    "Would call endpoint: https://example.com/createCapabilitySet with params\n"
                    + "{'setname': 'testcapabilityset', 'pattern': 'scope1,scope2'}"
                ),
                (
                    "Would call endpoint: https://example.com/addCapabilitySetToFQAN with params\n"
                    + "{'setname': 'testcapabilityset', 'unitname': 'testunit', 'role': 'myrole'}"
                ),
            ],
        ),
    ],
)
@pytest.mark.unit
def test_NewCapabiilitySet_run(args, expected, capsys):
    api = FerryAPI(
        base_url="https://example.com/",
        authorizer=Auth(),
        dryrun=True,
    )

    NewCapabilitySet().run(
        api=api,
        args=args,
    )

    captured = capsys.readouterr()
    for elt in expected:
        assert elt in captured.out


@pytest.mark.parametrize(
    "scopes_string, out_delimiter, expected",
    [
        ("scope1,scope2", ",", ["scope1", "scope2"]),
        ("scope1 scope2", " ", ["scope1", "scope2"]),
        ("scope1, scope2", ", ", ["scope1", "scope2"]),
        (
            "scope,1,scope2",
            ",",
            ["scope", "1", "scope2"],
        ),  # This is a malformed scope, but we want to test that it is handled correctly
    ],
)
@pytest.mark.unit
def test_scopes_string_to_list(scopes_string, out_delimiter, expected):
    assert (
        NewCapabilitySet.scopes_string_to_list(scopes_string, out_delimiter) == expected
    )


@pytest.mark.parametrize(
    "list1, list2, expected",
    [
        (["a", "b", "c"], ["c", "b", "a"], True),
        (["a", "b", "c"], ["a", "b"], False),
        (["a", "b", "c"], ["d", "e", "f"], False),
        ([], [], True),
        (["a"], ["a"], True),
        (["a"], [], False),
    ],
)
@pytest.mark.unit
def test_check_lists_for_same_elts(list1, list2, expected) -> bool:
    assert NewCapabilitySet._check_lists_for_same_elts(list1, list2) == expected


@pytest.mark.parametrize(
    "fqan, expected",
    [
        ("/org/exp1/Role=myrole/Capability=NULL", "myrole"),
        ("/org/Role=myrole/Capability=NULL", "myrole"),
        ("/org/role=myrole/Capability=NULL", ""),
        ("/org/myrole/Capability=NULL", ""),
        (
            "/org/Role=my/role/Capability=NULL",
            "my",
        ),  # This is a malformed FQAN, but we want to test that it is handled correctly
        ("randomstring", ""),
        ("", ""),
    ],
)
@pytest.mark.unit
def test_calculate_role(fqan, expected) -> str:
    assert NewCapabilitySet._calculate_role(fqan) == expected
