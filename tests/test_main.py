from collections import namedtuple
import io
import os
import pathlib
import subprocess
import sys

import pytest

from ferry_cli.ferry_cli import (
    FerryCLI,
    handle_show_configfile,
    get_config_info_from_user,
    help_called,
    normalize_endpoint,
)

import ferry_cli.ferry_cli as _main
import ferry_cli.config.config as _config


@pytest.fixture
def get_ferry_cli_path():
    root = pathlib.Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    bindir = root / "src" / "ferry_cli"
    return str((bindir / "ferry_cli.py").resolve())


@pytest.fixture
def install_mock_swagger_json_file(tmp_path):
    import os
    import shutil

    root = pathlib.Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    configdir = root / "src" / "ferry_cli" / "config"
    swagger_path = configdir / "swagger.json"
    try:
        old_file = shutil.move(swagger_path, tmp_path / "old_swagger.json")
    except FileNotFoundError:
        old_file = None
    with open(swagger_path, "w") as f:
        f.write(
            """
{
    "swagger": "2.0",
    "info": {},
    "paths" : {
        "/ping": {
            "get": {
                "description": "description",
                "consumes": [
                    "text/html"
                ],
                "produces": [
                    "application/json"
                ],
                "tags": [
                    "Users"
                ],
                "summary": "summary",
                "parameters": [ ],
                "responses": {
                    "200": {
                        "description": "OK",
                        "schema": {
                            "$ref": "#/definitions/main.jsonOutput"
                        }
                    }
                }
            }
        }
    }
}
                """
        )

    yield
    os.unlink(swagger_path)
    if old_file is not None:
        shutil.move(old_file, swagger_path)


@pytest.fixture
def inject_fake_stdin(monkeypatch):
    def inner(fake_input):
        monkeypatch.setattr("sys.stdin", io.StringIO(fake_input))

    return inner


@pytest.fixture
def mock_write_config_file_with_user_values(monkeypatch):
    def _func():
        print("Mocked write_config_file")

    monkeypatch.setattr(
        _main,
        "write_config_file_with_user_values",
        _func,
    )


@pytest.fixture
def write_and_set_fake_config_file(monkeypatch, tmp_path):
    # Fake config file
    p = tmp_path
    config_dir = p / "ferry_cli"
    config_dir.mkdir()
    config_file = config_dir / "config.ini"
    config_file.write_text("This is a fake config file")
    monkeypatch.setenv("XDG_CONFIG_HOME", str(p.absolute()))
    return config_file


@pytest.fixture
def configfile_doesnt_exist(monkeypatch):
    monkeypatch.setattr(_config, "get_configfile_path", lambda: None)


@pytest.mark.unit
def test_sanitize_base_url():
    cases = ["http://hostname.domain:1234/", "http://hostname.domain:1234"]
    expected = "http://hostname.domain:1234/"
    for case in cases:
        assert FerryCLI._sanitize_base_url(case) == expected

    complex_case = "http://hostname.domain:1234/apiEndpoint?key1=val1"
    assert FerryCLI._sanitize_base_url(complex_case) == complex_case


@pytest.mark.unit
def test_handle_show_configfile_configfile_exists(
    capsys, write_and_set_fake_config_file
):
    # If we have a config file, we should print out the path to the config file and return
    config_file = write_and_set_fake_config_file

    test_case = namedtuple("TestCase", ["args", "expected_stdout_substr"])
    args_cases = (
        test_case(
            ["--show-config-file", "--foo", "bar", "--baz"],  # Arg passed
            f"Configuration file: {str(config_file.absolute())}",
        ),
        test_case(["--foo", "bar", "--baz"], ""),  # Arg not passed
    )

    for case in args_cases:
        handle_show_configfile(case.args)
        captured = capsys.readouterr()
        assert captured.out.strip() == case.expected_stdout_substr


@pytest.mark.unit
def test_handle_show_configfile_configfile_does_not_exist(
    capsys, monkeypatch, tmp_path, mock_write_config_file_with_user_values
):
    # If we can't find the configfile, we should print out the right message and enter interactive mode
    p = tmp_path
    config_dir = p / "ferry_cli"
    config_dir.mkdir()
    monkeypatch.setenv("XDG_CONFIG_HOME", str(p.absolute()))

    args = ["--show-config-file", "--foo", "bar", "--baz"]  # Arg passed

    handle_show_configfile(args)
    captured = capsys.readouterr()
    assert (
        f"Based on the environment, would use configuration file: {str((config_dir / 'config.ini').absolute())}.  However, that path does not exist. Will now enter interactive mode to generate it."
        in captured.out
    )
    assert "Mocked write_config_file" in captured.out


@pytest.mark.unit
def test_handle_show_configfile_envs_not_found(
    capsys,
    configfile_doesnt_exist,
    mock_write_config_file_with_user_values,
):
    args = ["--show-config-file", "--foo", "bar", "--baz"]  # Arg passed

    handle_show_configfile(args)
    captured = capsys.readouterr()
    assert (
        "No configuration file found.  Will attempt to create configuration file at $HOME/.config/ferry_cli/config.ini"
        in captured.out
    )
    assert "Mocked write_config_file" in captured.out


@pytest.mark.parametrize(
    "args, expected_out_substr",
    [
        (
            ["-h"],
            "--show-config-file",
        ),  # If we pass -h, make sure --show-config-file shows up
        (
            ["-h", "--show-config-file", "-e", "getAllGroups"],
            "--show-config-file",
        ),  # If we pass -h and --show-config-file, -h should win
        (
            ["--show-config-file"],
            "Configuration file",
        ),  # Print out config file if we only pass --show-config-file
        (
            ["--show-config-file", "-e", "getAllGroups"],
            "Configuration file",
        ),  # If we pass --show-config-file with other args, --show-config-file should print out the config file
    ],
)
@pytest.mark.unit
def test_show_configfile_flag_with_other_args(
    install_mock_swagger_json_file,
    get_ferry_cli_path,
    write_and_set_fake_config_file,
    args,
    expected_out_substr,
):
    # Since we have to handle --show-config-file outside of argparse, make sure we get the correct behavior given different combinations of args
    exe_args = [sys.executable, get_ferry_cli_path]
    exe_args.extend(args)

    try:
        proc = subprocess.run(exe_args, capture_output=True)
    except SystemExit:
        pass
    assert expected_out_substr in str(proc.stdout)


@pytest.mark.unit
def test_get_config_info_from_user(monkeypatch, capsys):
    # test good
    monkeypatch.setattr("builtins.input", lambda _: "https://wwww.google.com")
    correct_dict = {"base_url": "https://wwww.google.com"}
    generated_dict = get_config_info_from_user()
    assert correct_dict == generated_dict

    with pytest.raises(SystemExit) as pytest_wrapped_e:
        monkeypatch.setattr("builtins.input", lambda _: "badurl")
        get_config_info_from_user()
        assert pytest_wrapped_e.from_e == 1

    captured = capsys.readouterr()
    assert (
        "\nThis doesn't look like a valid URL, you need to specify the https:// part. Try again."
        in captured.out
    )
    assert "\nMultiple failures in specifying base URL, exiting..." in captured.out


@pytest.mark.unit
def test_help_called():
    # Test when "--help" is present in the arguments
    args = ["command", "--help", "arg1", "-h", "arg2"]
    assert help_called(args) == True

    # Test when "-h" is present in the arguments
    args = ["command", "arg1", "-h", "arg2", "--help"]
    assert help_called(args) == True

    # Test when neither "--help" nor "-h" is present in the arguments
    args = ["command", "arg1", "arg2"]
    assert help_called(args) == False


@pytest.mark.parametrize(
    "expected_stdout_before_prompt, user_input, expected_stdout_after_prompt",
    [
        (
            "Configuration file already exists at",
            "n",
            ["usage:", "Exiting without writing configuration file."],
        ),
        (
            "Configuration file already exists at",
            "\n",
            ["usage:", "Exiting without writing configuration file."],
        ),
        (
            "Configuration file already exists at",
            "y",
            ["usage:", "Exiting without writing configuration file."],
        ),
        (
            "Configuration file already exists at",
            "Y",
            [
                "Will launch interactive mode to write configuration file.  If this was a mistake, just press Ctrl+C to exit",
                "Mocked write_config_file",
            ],
        ),
    ],
)
@pytest.mark.unit
def test_handle_no_args_configfile_exists(
    mock_write_config_file_with_user_values,
    capsys,
    inject_fake_stdin,
    write_and_set_fake_config_file,
    expected_stdout_before_prompt,
    user_input,
    expected_stdout_after_prompt,
):
    inject_fake_stdin(user_input)
    config_file = write_and_set_fake_config_file

    with pytest.raises(SystemExit) as pytest_wrapped_e:
        _main.handle_no_args(config_file)

    captured = capsys.readouterr()
    assert expected_stdout_before_prompt in captured.out
    for elt in expected_stdout_after_prompt:
        assert elt in captured.out

    assert pytest_wrapped_e.type == SystemExit
    assert pytest_wrapped_e.value.code == 0


@pytest.mark.parametrize(
    "expected_stdout_before_prompt, user_input, expected_stdout_after_prompt",
    [
        (
            "Would you like to enter interactive mode to write the configuration file for ferry-cli to use in the future (Y/[n])? ",
            "n",
            ["usage:"],
        ),
        (
            "Would you like to enter interactive mode to write the configuration file for ferry-cli to use in the future (Y/[n])? ",
            "\n",
            ["usage:"],
        ),
        (
            "Would you like to enter interactive mode to write the configuration file for ferry-cli to use in the future (Y/[n])? ",
            "y",
            ["usage:"],
        ),
        (
            "Would you like to enter interactive mode to write the configuration file for ferry-cli to use in the future (Y/[n])? ",
            "Y",
            [
                "Will launch interactive mode to write configuration file.  If this was a mistake, just press Ctrl+C to exit",
                "Mocked write_config_file",
            ],
        ),
    ],
)
@pytest.mark.unit
def test_handle_no_args_configfile_does_not_exist(
    configfile_doesnt_exist,
    capsys,
    inject_fake_stdin,
    mock_write_config_file_with_user_values,
    expected_stdout_before_prompt,
    user_input,
    expected_stdout_after_prompt,
):
    inject_fake_stdin(user_input)

    with pytest.raises(SystemExit) as pytest_wrapped_e:
        _main.handle_no_args(None)

    captured = capsys.readouterr()
    assert expected_stdout_before_prompt in captured.out
    for elt in expected_stdout_after_prompt:
        assert elt in captured.out

    assert pytest_wrapped_e.type == SystemExit
    assert pytest_wrapped_e.value.code == 0


@pytest.mark.unit
def test_snakecase_and_underscore_conversion():
    test_endpoints = {"getUserInfo": object()}

    # test to make sure function does matching irrespective of capitalization
    assert normalize_endpoint(test_endpoints, "Get_USeriNFo") == "getUserInfo"

    # test to make sure function never stops working for correct syntax
    assert normalize_endpoint(test_endpoints, "getUserInfo") == "getUserInfo"

    # test that non-endpoint values are left untouched when no match is found
    assert (
        normalize_endpoint(test_endpoints, "SomeOtherEndpoint") == "SomeOtherEndpoint"
    )


@pytest.mark.unit
def test_leading_underscore_preserved():
    test_endpoints = {"_internalEndpoint": object()}

    assert (
        normalize_endpoint(test_endpoints, "_Internal_endpoint") == "_internalEndpoint"
    )


@pytest.mark.parametrize(
    "base_url, expected_base_url",
    [
        (None, "https://example.com:12345/"),  # Get base_url from config
        (
            "https://override_example.com:54321/",
            "https://override_example.com:54321/",
        ),  # Get base_url from override
    ],
)
@pytest.mark.unit
def test_override_base_url_FerryCLI(tmp_path, base_url, expected_base_url):
    # Set up fake config
    fake_config_text = """
[api]
base_url = https://example.com:12345/
dev_url = https://example.com:12345/

"""
    fake_config = tmp_path / "config.ini"
    fake_config.write_text(fake_config_text)

    cli = FerryCLI(config_path=fake_config, base_url=base_url)
    assert cli.base_url == expected_base_url


@pytest.mark.parametrize(
    "args, expected_out_url",
    [
        ([], "https://example.com:12345/"),  # Get base_url from config
        (
            ["--server", "https://override_example.com:54321/"],
            "https://override_example.com:54321/",
        ),  # Get base_url from override
    ],
)
@pytest.mark.integration
def test_server_flag_main(
    tmp_path,
    monkeypatch,
    install_mock_swagger_json_file,
    get_ferry_cli_path,
    args,
    expected_out_url,
):
    # Run ferry-cli with overridden base_url in dryrun mode to endpoint ping. Then see if we see the correct server in output
    # Set up fake config
    fake_config_text = """
[api]
base_url = https://example.com:12345/
dev_url = https://example.com:12345/

"""
    # Fake config file
    p = tmp_path
    config_dir = p / "ferry_cli"
    config_dir.mkdir()
    config_file = config_dir / "config.ini"
    config_file.write_text(fake_config_text)
    monkeypatch.setenv("XDG_CONFIG_HOME", str(p.absolute()))

    exe_args = [sys.executable, get_ferry_cli_path]
    exe_args.extend(args + ["--dryrun", "-e", "ping"])

    proc = subprocess.run(exe_args, capture_output=True)
    assert f"Would call endpoint: {expected_out_url}ping with params" in str(
        proc.stdout
    )
