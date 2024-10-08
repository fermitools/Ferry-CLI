# MIT License
#
# Copyright (c) 2024, FERMI NATIONAL ACCELERATOR LABORATORY
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.


import os
from spack.package import *


class FerryCli(PythonPackage):
    """
    FA command line interface for making ferry api calls.
    Can be used to automate repetitive tasks, incorporate
    usage safeguards for users or groups, or create and
    execute scripts for common sequences.
    """

    homepage = "https://github.com/fermitools/Ferry-CLI"
    git = "https://github.com/fermitools/Ferry-CLI.git"

    maintainers = ["ltrestka", "shreyb", "cathulhu"]

    version("latest", branch="master")
    version("1.0.0", tag="1.0.0")
    version("1.0.1", tag="1.0.1", preferred=True)

    depends_on("python@3.6.8:", type=("run"))
    
    python_packages = [
        "certifi",
        "charset-normalizer",
        "idna",
        "requests",
        "urllib3",
        "setuptools",
        "validators"
    ]

    def install(self, spec, prefix):
        install_tree(self.stage.source_path, prefix)
        
        pip = which('pip')
        for package in self.python_packages:
            pip('install', package, '--prefix', prefix)
        
        # Update the wrapper script to support whichever python interpreter is being used
        wrapper_content = None
        script_path = os.path.join(prefix, 'bin', 'ferry-cli')
        with open(script_path, 'r') as f:
            wrapper_content = f.read()
            f.close()
        if wrapper_content:
            print(wrapper_content)
            wrapper_content = wrapper_content.replace("/usr/bin/python3", spec['python'].command.path)
            with open(script_path, 'w') as f:
                f.write(wrapper_content)
                f.close()
                
        # Make the wrapper script executable
        chmod = which('chmod')
        chmod('+x', script_path)

    def setup_environment(self, spack_env, run_env):
        run_env.prepend_path("PATH", self.prefix.bin)
        run_env.prepend_path("PYTHONPATH", self.prefix.lib)

    def url_for_version(self, version):
        url = "https://github.com/fermitools/Ferry-CLI/archive/refs/tags/{0}.tar.gz"
        return url.format(version)
