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

    version("master", branch="master")
    version("0.1.0", branch="spack_deployment", preferred=True)

    depends_on("python@3.6.8:", type=("run"))
    depends_on("py-pip", type=("build", "run"))
    depends_on("py-certifi", type=("build", "run"))
    depends_on("py-charset-normalizer", type=("build", "run"))
    depends_on("py-idna@3.4:", type=("build", "run"))
    depends_on("py-requests@2.31.0:", type=("build", "run"))
    depends_on("py-urllib3", type=("build", "run"))
    depends_on("py-setuptools", type=("build", "run"))
    depends_on("py-validators", type=("build", "run"))

    def install(self, spec, prefix):
        install_tree(self.stage.source_path, prefix)

    def setup_environment(self, spack_env, run_env):
        run_env.prepend_path("PATH", self.prefix.bin)
