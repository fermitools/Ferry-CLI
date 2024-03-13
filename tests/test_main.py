from collections import namedtuple
import os
import subprocess
import sys
import pytest

from ferry_cli.__main__ import FerryCLI, handle_show_configfile, get_config_info_from_user
import ferry_cli.config.config as _config


@pytest.mark.unit
def test_sanitize_base_url():
    cases = ["http://hostname.domain:1234/", "http://hostname.domain:1234"]
    expected = "http://hostname.domain:1234/"
    for case in cases:
        assert FerryCLI._sanitize_base_url(case) == expected

    complex_case = "http://hostname.domain:1234/apiEndpoint?key1=val1"
    assert FerryCLI._sanitize_base_url(complex_case) == complex_case


@pytest.mark.unit
def test_handle_show_configfile_configfile_exists(capsys, monkeypatch, tmp_path):
    p = tmp_path
    config_dir = p / "ferry_cli"
    config_dir.mkdir()
    config_file = config_dir / "config.ini"
    config_file.write_text("This is a fake config file")
    monkeypatch.setenv("XDG_CONFIG_HOME", str(p.absolute()))

    test_case = namedtuple("TestCase", ["args", "expected_stdout_substr"])
    args_cases = (
        test_case(
            ["--show-config-file", "--foo", "bar", "--baz"],  # Arg passed
            f"Configuration file: {str(config_file.absolute())}",
        ),
        test_case(["--foo", "bar", "--baz"], ""),  # Arg not passed
    )

    for case in args_cases:
        try:
            handle_show_configfile(case.args)
        except SystemExit:
            pass
        captured = capsys.readouterr()
        assert captured.out.strip() == case.expected_stdout_substr


@pytest.mark.unit
def test_handle_show_configfile_configfile_does_not_exist(
    capsys, monkeypatch, tmp_path
):
    p = tmp_path
    config_dir = p / "ferry_cli"
    config_dir.mkdir()
    monkeypatch.setenv("XDG_CONFIG_HOME", str(p.absolute()))

    args = ["--show-config-file", "--foo", "bar", "--baz"]  # Arg passed

    try:
        handle_show_configfile(args)
    except SystemExit:
        pass
    captured = capsys.readouterr()
    assert (
        captured.out.strip()
        == f"Based on the environment, would use configuration file: {str((config_dir / 'config.ini').absolute())}.  However, that path does not exist."
    )


@pytest.mark.unit
def test_handle_show_configfile_not_found(capsys, monkeypatch):
    monkeypatch.setattr(_config, "get_configfile_path", lambda: None)

    args = ["--show-config-file", "--foo", "bar", "--baz"]  # Arg passed

    try:
        handle_show_configfile(args)
    except SystemExit:
        pass
    captured = capsys.readouterr()
    assert (
        captured.out.strip()
        == 'No configuration file found.'
    )


# Since we have to handle --show-config-file outside of argparse, make sure we get the correct behavior
@pytest.mark.unit
def test_show_configfile_flag_with_other_args():
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
            [sys.executable, exe, "--show-config-file", "-e", "getAllGroups"], "Configuration file"
        ),  # If we pass --show-config-file with other args, --show-config-file should win
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
    
    