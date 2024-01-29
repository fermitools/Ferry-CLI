from setuptools import setup, find_packages
from version import print_version, get_summary
setup(
    name='Ferry CLI',
    version=print_version(short=True),
    author='Lucas Trestka, Shreyas Bhat, Lydia Brynmoor',
    author_email='ltrestka@fnal.gov, sbhat@fnal.gov, brynmoor@fnal.gov',
    description=get_summary(),
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/fermitools/Ferry-CLI', 
    packages=find_packages(exclude=('tests',)),
    install_requires=[
        'certifi>=2023.11.17',
        'charset-normalizer>=3.3.2',
        'idna>=3.4',
        'requests>=2.31.0',
        'toml>=0.10.2',
        'urllib3>=2.1.0',
    ],
    classifiers=[
        'Programming Language :: Python :: 3.6+', 
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.6',
)
