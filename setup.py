from setuptools import setup, find_packages
from ferry_cli.version import print_version, get_summary

with open("README.md", "r") as file:
    long_desc = file.read()
setup(
    name="ferry_cli",
    version=print_version(short=True),
    author="Lucas Trestka, Shreyas Bhat, Lydia Brynmoor",
    author_email="ltrestka@fnal.gov, sbhat@fnal.gov, brynmoor@fnal.gov",
    description=get_summary(),
    long_description=long_desc,
    long_description_content_type="text/markdown",
    url="https://github.com/fermitools/Ferry-CLI",
    packages=find_packages(exclude=["tests", "remove"]),
    include_package_data=True,
    package_data={
        "ferry_cli": [
            "ferry_cli/version.py",
            "ferry_cli/config",
            "ferry_cli/helpers",
            "ferry_cli/safeguards",
        ],
        "helpers": [
            "ferry_cli/supported_workflows",
            "ferry_cli/helpers/api.py",
            "ferry_cli/helpers/auth.py",
            "ferry_cli/helpers/customs.py",
            "ferry_cli/helpers/workflows.py",
        ],
        "helpers.supported_workflows": [
            "ferry_cli/helpers/supported_workflows/CloneResource.py",
            "ferry_cli/helpers/supported_workflows/GetFilteredGroupInfo.py",
        ],
        "safeguards": ["ferry_cli/safeguards/dcs.py"],
        "config": ["ferry_cli/config/config.toml", "ferry_cli/config/swagger.json"],
    },
    install_requires=[
        "certifi>=2023.11.17",
        "charset-normalizer>=3.3.2",
        "idna>=3.4",
        "requests>=2.31.0",
        "toml>=0.10.2",
        "urllib3>=2.1.0",
    ],
    classifiers=[
        "Programming Language :: Python :: 3.6+",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
    entry_points={
        "console_scripts": [
            "ferry-cli=ferry_cli.__main__:main",
        ],
    },
)
