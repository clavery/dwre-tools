import re
import pytest
import responses
import json

from dwre_tools.api.instance import SFCCInstance

@pytest.fixture
def example_env():
    return {
        "server": "test.demandware.com",
        "username": "chuck",
        "password": "chuck",
        "codeVersion": "the_code_version",
    }


def test_create_instance_from_env(example_env):
    instance = SFCCInstance.from_env(example_env)
    assert(instance.server == "test.demandware.com")

