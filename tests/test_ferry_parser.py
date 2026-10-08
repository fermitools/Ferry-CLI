import pytest

from ferry_cli.helpers.ferry_parser import FerryParser


@pytest.mark.parametrize("description", ["", "   ", "\n\t "])
def test_parse_description_blank(description):
    """A blank description should not abort endpoint generation."""
    result = FerryParser.parse_description(
        name="testEndpoint", method="GET", description=description
    )
    assert "testEndpoint" in result
    assert "(GET)" in result


def test_parse_description_wraps_long_text():
    description = "word " * 40
    result = FerryParser.parse_description(
        name="testEndpoint", method="GET", description=description
    )
    assert len(result.splitlines()) > 1


def test_set_arguments_with_blank_param_description():
    """Swagger parameters sometimes carry an empty description."""
    parser = FerryParser.create(description="test")
    parser.set_arguments(
        [{"name": "unitname", "type": "string", "required": False, "description": ""}]
    )
    args = parser.parse_args(["--unitname", "testunit"])
    assert args.unitname == "testunit"
