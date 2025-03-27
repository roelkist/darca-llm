# tests/test_llm.py

from unittest.mock import MagicMock, patch

import openai  # ✅ Fix: import openai so we can subclass OpenAIError
import pytest

from darca_llm import (
    AIClient,
    BaseLLMClient,
    LLMAPIKeyMissing,
    LLMContentFormatError,
    LLMException,
    LLMResponseError,
    OpenAIClient,
)


def test_base_llm_client_get_raw_response_executes_base_pass():
    """
    Ensure BaseLLMClient.get_raw_response() is executed via super() to hit
    the abstract pass line.
    """

    class DummyClient(BaseLLMClient):
        def get_raw_response(self, *args, **kwargs):
            return super().get_raw_response(
                *args, **kwargs
            )  # 👈 Will hit the base `pass`

    DummyClient.__abstractmethods__ = set()
    client = DummyClient()

    result = client.get_raw_response("sys", "user")
    assert (
        result is None
    )  # ✅ NotImplementedError is not raised because method is pass


def test_ai_client_default_backend(openai_key):
    client = AIClient()
    assert isinstance(client._client, OpenAIClient)


def test_ai_client_unsupported_backend():
    with pytest.raises(LLMException) as e:
        AIClient(backend="llama")
    assert "unsupported" in str(e.value).lower()


def test_openai_client_missing_key():
    with patch.dict("os.environ", {}, clear=True):
        with pytest.raises(LLMAPIKeyMissing) as e:
            OpenAIClient()
        assert "OPENAI_API_KEY" in str(e.value)


def test_openai_get_raw_response_success(openai_key):
    mock_response = MagicMock()
    mock_response.choices[0].message.content = "Mocked response"

    with patch("openai.chat.completions.create", return_value=mock_response):
        client = OpenAIClient()
        result = client.get_raw_response("You are helpful.", "Say hi.")
        assert result == "Mocked response"


def test_openai_get_raw_response_openai_error(openai_key):
    class FakeOpenAIError(openai.OpenAIError):
        pass

    with patch(
        "openai.chat.completions.create",
        side_effect=FakeOpenAIError("Simulated failure"),
    ):
        client = OpenAIClient()
        with pytest.raises(LLMResponseError) as e:
            client.get_raw_response("sys", "user")
        assert (
            e.value.error_code == "LLM_API_REQUEST_FAILED"
        )  # ✅ Assert specific code
        assert (
            "returned an error" in e.value.message.lower()
        )  # ✅ Flexible string check


def test_openai_get_raw_response_unexpected_error(openai_key):
    mock_response = MagicMock()
    mock_response.choices = [{}]  # Missing `.message.content`

    with patch("openai.chat.completions.create", return_value=mock_response):
        client = OpenAIClient()
        with pytest.raises(LLMResponseError) as e:
            client.get_raw_response("sys", "user")
        assert "parse" in str(e.value).lower()
        assert isinstance(e.value.cause, Exception)


def test_file_content_response_valid(openai_key):
    mock_response = MagicMock()
    mock_response.choices[0].message.content = "File processed"

    with patch("openai.chat.completions.create", return_value=mock_response):
        client = OpenAIClient()
        file_data = (
            "name: test"  # ✅ Avoid block prefix,to ensure single-block
        )
        result = client.get_file_content_response("sys", file_data)
        assert "File processed" in result


def test_file_content_response_invalid(openai_key):
    client = OpenAIClient()
    bad_file = '"""yaml\nkey: value\n"""\n"""yaml\nanother: block\n"""'
    with pytest.raises(LLMContentFormatError) as e:
        client.get_file_content_response("sys", bad_file)
    assert "multiple" in str(e.value).lower()


def test_delegation_via_getattr(openai_key):
    ai = AIClient()
    assert hasattr(ai, "get_raw_response")
