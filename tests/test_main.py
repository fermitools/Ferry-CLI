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


@pytest.mark.unit
def test_set_config_value_ok(fake_config_path):
    p = fake_config_path
    c = FerryCLI(p)
    c._set_config_value("api.base_url", "baz")

    new_cfg = configparser.ConfigParser()
    with open(p, "r") as f:
        new_cfg.read_file(f)

    assert new_cfg["api"]["base_url"] == "baz"
    assert new_cfg["foo"]["bar"] == "baz"
    assert new_cfg["spam"]["bacon"] == "eggs"


@pytest.mark.unit
def test_set_config_value_bad_key(fake_config_path):
    p = fake_config_path
    c = FerryCLI(p)
    with pytest.raises(KeyError, match="Unsupported configuration key"):
        c._set_config_value("foo.bar", "baz")


@pytest.mark.unit
def test_set_config_value_arg_good(fake_config_path, capsys):
    p = fake_config_path
    c = FerryCLI(fake_config_path)
    parser = c.get_arg_parser()
    try:
        parser.parse_args(["--set-config-value", "api.base_url=spam"])
    except SystemExit:
        pass
    captured = capsys.readouterr()
    assert captured.out == "Set api.base_url to value spam\n"

    new_cfg = configparser.ConfigParser()
    with open(p, "r") as f:
        new_cfg.read_file(f)

    assert new_cfg["api"]["base_url"] == "spam"


@pytest.mark.unit
def test_set_config_value_arg_bad(fake_config_path, capsys):
    p = fake_config_path
    c = FerryCLI(fake_config_path)
    parser = c.get_arg_parser()
    with pytest.raises(
        Exception,
        match="No configuration option exists, or the option is not supported: foo",
    ):
        parser.parse_args(["--set-config-value", "foo=spam"])
