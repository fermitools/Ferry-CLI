import os

import pytest


@pytest.fixture
def stash_env(monkeypatch):
    def inner(env_var):
        env_previous = os.getenv(env_var)
        monkeypatch.delenv(env_var, raising=False)
        yield
        if env_previous:
            os.environ[env_var] = env_previous

    return inner
