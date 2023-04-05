import os
from unittest import mock

import pytest
from pydantic import SecretStr

from ..agents import GCPCloudRunAgent
from ..config import Config


@pytest.fixture
def mock_env_vars() -> dict:
    env = dict(
        GITHUB_APP__NAME="pytest-app",
        GITHUB_APP__ID="123",
        GITHUB_APP__WEBHOOK_SECRET="abcde",
        GITHUB_APP__PRIVATE_KEY="""
        -----BEGIN RSA PRIVATE KEY-----
        abcabcabcabcabcabcabcabcabcabcab
        -----END RSA PRIVATE KEY-------
        """,
        AGENT__CLS="service.agents.GCPCloudRunAgent",
        AGENT__SERVICE_URL="https://cloud.run.url.com",
        AGENT__INVOKER_KEYFILE="/path/to/key.json",
    )
    with mock.patch.dict(os.environ, env):
        yield env


def test_config(mock_env_vars: dict[str, str]):
    c = Config()

    github_app_vars = {
        k: v for k, v in mock_env_vars.items() if k.startswith("GITHUB_APP")
    }
    # Config.github_app fields are passed 1:1 from env vars by name, so these
    # can be checked by iterating through the items of this dict. 
    for k, v in github_app_vars.items():
        field, subfield = k.split("__")
        attr = getattr(getattr(c, field.lower()), subfield.lower())

        if k == "GITHUB_APP__NAME":
            assert attr == v
        elif k == "GITHUB_APP__ID":
            assert attr == int(v)
        elif k in ("GITHUB_APP__WEBHOOK_SECRET", "GITHUB_APP__PRIVATE_KEY"):
            assert isinstance(attr, SecretStr)
            assert attr.get_secret_value() == v
        else:
            # make sure we didn't miss something
            raise ValueError
    
    # Config.agent is parsed into an instance of the provided class, so we check
    # this differently than we did the Config.github_app above.
    assert isinstance(c.agent, GCPCloudRunAgent)
    assert c.agent.service_url == mock_env_vars["AGENT__SERVICE_URL"]
    assert c.agent.invoker_keyfile == mock_env_vars["AGENT__INVOKER_KEYFILE"]
