import os

import pytest


@pytest.fixture
def stash_env():
    def inner(env_var):
        env_previous = os.getenv(env_var)
        if env_previous:
            del os.environ[env_var]
        print(os.environ.get(env_var))
        yield
        if env_previous:
            os.environ[env_var] = env_previous

    return inner
