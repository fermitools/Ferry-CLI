# Copyright 2013-2023 Lawrence Livermore National Security, LLC and other
# Spack Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)

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

    version("master",  branch="master")
    version("0.1.0", branch="spack_deployment", preferred=True)
    
    depends_on("python@3.6.8:", type=("run"))
    depends_on("py-pip", type=("build", "run"))
    depends_on("py-certifi", type=("build", "run"))
    depends_on("py-charset-normalizer", type=("build", "run"))
    depends_on("py-idna@3.4:", type=("build", "run"))
    depends_on("py-requests@2.31.0:", type=("build", "run"))
    depends_on("py-urllib3", type=("build", "run"))
    depends_on("py-setuptools", type=("build", "run"))

    def install(self, spec, prefix):
        install_tree(self.stage.source_path, prefix)

    def setup_environment(self, spack_env, run_env):
        run_env.prepend_path("PATH", self.prefix.bin)
        