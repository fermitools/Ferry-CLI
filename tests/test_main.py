from collections import namedtuple
import io
import os
import subprocess
import sys
import pytest

from ferry_cli.__main__ import (
    FerryCLI,
    handle_show_configfile,
    get_config_info_from_user,
    help_called,
)
import ferry_cli.__main__ as _main
import ferry_cli.config.config as _config


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
    capsys, monkeypatch, write_and_set_fake_config_file
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
    monkeypatch,
    mock_write_config_file_with_user_values,
):
    # If the envs don't allow get_configfile_path to find the config file, we should print out the right message and enter interactive mode
    monkeypatch.setattr(_config, "get_configfile_path", lambda: None)

    args = ["--show-config-file", "--foo", "bar", "--baz"]  # Arg passed

    handle_show_configfile(args)
    captured = capsys.readouterr()
    assert (
        "No configuration file found.  Will attempt to create configuration file at $HOME/.config/ferry_cli/config.ini"
        in captured.out
    )
    assert "Mocked write_config_file" in captured.out


@pytest.mark.unit
def test_show_configfile_flag_with_other_args(
    tmp_path, monkeypatch, write_and_set_fake_config_file
):
    # Since we have to handle --show-config-file outside of argparse, make sure we get the correct behavior given different combinations of args
    bindir = f"{os.path.dirname(os.path.dirname(os.path.abspath(__file__)))}/bin"
    exe = f"{bindir}/ferry-cli"

    test_case = namedtuple("TestCase", ["args", "expected_out_substr"])

    cases = (
        test_case(
            [sys.executable, exe, "-h"], "--show-config-file"
        ),  # If we pass -h, make sure --show-config-file shows up
        test_case(
            [sys.executable, exe, "-h", "--show-config-file", "-e", "getAllGroups"],
            "--show-config-file",
        ),  # If we pass -h and --show-config-file, -h should win
        test_case(
            [sys.executable, exe, "--show-config-file"], "Configuration file"
        ),  # Print out config file if we only pass --show-config-file
        test_case(
            [sys.executable, exe, "--show-config-file", "-e", "getAllGroups"],
            "Configuration file",
        ),  # If we pass --show-config-file with other args, --show-config-file should print out the config file
    )

    for case in cases:
        try:
            proc = subprocess.run(case.args, capture_output=True)
        except SystemExit:
            pass
        assert case.expected_out_substr in str(proc.stdout)


@pytest.mark.unit
def test_get_config_info_from_user(monkeypatch, capsys):
    # test good
    monkeypatch.setattr('builtins.input', lambda _: "https://wwww.google.com")

    correct_dict = {"base_url" : "https://wwww.google.com"}
    generated_dict = get_config_info_from_user()

    assert(correct_dict == generated_dict)

    with pytest.raises(SystemExit) as pytest_wrapped_e:
        monkeypatch.setattr('builtins.input', lambda _: "https://wwww.google.")
        get_config_info_from_user()
        assert(pytest_wrapped_e.from_e == 1)
    
    
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
    "user_input, expected_stdout_after_prompt",
    [
        ("n", "Exiting without overwriting configuration file."),
        ("\n", "Exiting without overwriting configuration file."),
        ("y", "Exiting without overwriting configuration file."),
        (
            "Y",
            "Will launch interactive mode to rewrite configuration file.  If this was a mistake, just press Ctrl+C to exit.\nMocked write_config_file",
        ),
    ],
)
@pytest.mark.unit
def test_handle_no_args_configfile_exists_Y(
    monkeypatch,
    tmp_path,
    mock_write_config_file_with_user_values,
    capsys,
    inject_fake_stdin,
    write_and_set_fake_config_file,
    user_input,
    expected_stdout_after_prompt,
):
    inject_fake_stdin(user_input)
    config_file = write_and_set_fake_config_file

    with pytest.raises(SystemExit) as pytest_wrapped_e:
        _main.handle_no_args(config_file)

    captured = capsys.readouterr()
    assert (
        "Configuration file already exists. Are you sure you want to overwrite it (Y/[n])?  "
        in captured.out
    )

    assert expected_stdout_after_prompt in captured.out
    assert pytest_wrapped_e.type == SystemExit
    assert pytest_wrapped_e.value.code == 0
