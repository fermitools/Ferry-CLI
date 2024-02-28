import configparser

import pytest

from ferry_cli.__main__ import FerryCLI


@pytest.fixture
def fake_config_path(tmp_path):
    config_file = tmp_path / "config.ini"
    config_file.write_text(
        """
[api]
base_url=foobar

[foo]
bar=baz

[spam]
bacon=eggs
"""
    )
    return config_file


@pytest.mark.unit
def test_sanitize_base_url():
    cases = ["http://hostname.domain:1234/", "http://hostname.domain:1234"]
    expected = "http://hostname.domain:1234/"
    for case in cases:
        assert FerryCLI._sanitize_base_url(case) == expected

    complex_case = "http://hostname.domain:1234/apiEndpoint?key1=val1"
    assert FerryCLI._sanitize_base_url(complex_case) == complex_case


@pytest.mark.unit
def test_get_config_value_arg_good(fake_config_path, capsys):
    c = FerryCLI(fake_config_path)
    parser = c.get_arg_parser()
    try:
        parser.parse_args(["--get-config-value", "foo.bar"])
    except SystemExit:
        pass
    captured = capsys.readouterr()
    assert captured.out == "baz\n"


@pytest.mark.unit
def test_get_config_value_arg_bad(fake_config_path, capsys):
    c = FerryCLI(fake_config_path)
    parser = c.get_arg_parser()
    with pytest.raises(Exception, match="No configuration option"):
        parser.parse_args(["--get-config-value", "doesnt.exist"])
