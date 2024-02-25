import os

import pytest


@pytest.fixture
def stash_env():
    def inner(env_var):
        xdg_previous = os.getenv(env_var)
        yield
        if xdg_previous:
            os.environ[env_var] = xdg_previous

    return inner
