# tests/conftest.py

import pytest
from unittest.mock import patch


@pytest.fixture
def openai_key():
    """
    Patch environment with a dummy OPENAI_API_KEY for each test.
    """
    with patch.dict("os.environ", {"OPENAI_API_KEY": "sk-test"}):
        yield
