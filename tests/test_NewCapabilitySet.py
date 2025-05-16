import pytest

from ferry_cli.helpers.api import FerryAPI
from ferry_cli.helpers.auth import Auth
from ferry_cli.helpers.supported_workflows.NewCapabilitySet import NewCapabilitySet


@pytest.mark.unit
def test_NewCapabiilitySet_run(capsys):
    endpoint = "https://example.com"
    args = {
        "groupname": "testgroup",
        "gid": 1234,
        "unitname": "testunit",
        "fqan": "/org/Role=myrole/Capability=NULL",
        "setname": "testcapabilityset",
        "scopes_pattern": "scope1,scope2",
    }
    role = "myrole"

    expected_output = [
        (
            f"Would call endpoint: {endpoint}/createGroup with params\n"
            + f"{{'groupname': '{args['groupname']}', 'gid': {args['gid']}, 'grouptype': 'UnixGroup'}}"
        ),
        (
            f"Would call endpoint: {endpoint}/addGroupToUnit with params\n"
            + f"{{'groupname': '{args['groupname']}', 'unitname': '{args['unitname']}', 'grouptype': 'UnixGroup'}}"
        ),
        (
            f"Would call endpoint: {endpoint}/createFQAN with params\n"
            + f"{{'fqan': '{args['fqan']}', 'unitname': '{args['unitname']}', 'groupname': '{args['groupname']}'}}"
        ),
        (
            f"Would call endpoint: {endpoint}/createCapabilitySet with params\n"
            + f"{{'setname': '{args['setname']}', 'pattern': '{args['scopes_pattern']}'}}"
        ),
        (
            f"Would call endpoint: {endpoint}/addCapabilitySetToFQAN with params\n"
            + f"{{'setname': '{args['setname']}', 'unitname': '{args['unitname']}', 'role': '{role}'}}"
        ),
    ]

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
    for elt in expected_output:
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
