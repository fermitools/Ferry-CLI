import os

from requests import Session
import pytest

from ferry_cli.helpers.auth import Auth


class fakeAuth(Auth):
    def __init__(self):
        pass

    def __call__(self, s: Session) -> Session:
        return s


@pytest.fixture
def stash_env(monkeypatch):
    def inner(env_var):
        env_previous = os.getenv(env_var)
        monkeypatch.delenv(env_var, raising=False)
        yield
        if env_previous:
            os.environ[env_var] = env_previous

    return inner
