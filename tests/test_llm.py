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
    """
    Test valid response from get_file_content_response with a single valid block.
    """
    mock_response = MagicMock()
    mock_response.choices[0].message.content = "```python\nprint('Hello World')\n```"

    with patch("openai.chat.completions.create", return_value=mock_response):
        client = OpenAIClient()
        user_prompt = "Provide the content of a simple Python file."
        
        # Calling the refactored method
        result = client.get_file_content_response("sys", user_prompt)
        
        assert result == "print('Hello World')"  # Ensure markdown prefix is stripped


def test_file_content_response_invalid(openai_key):
    """
    Test invalid response from get_file_content_response when multiple blocks are returned.
    """
    mock_response = MagicMock()
    mock_response.choices[0].message.content = (
        "```python\nprint('Hello World')\n```\n\n"
        "```python\nprint('Goodbye World')\n```"
    )

    with patch("openai.chat.completions.create", return_value=mock_response):
        client = OpenAIClient()
        user_prompt = "Provide the content of two Python files."
        
        # Ensure that an exception is raised for multiple blocks
        with pytest.raises(LLMContentFormatError) as e:
            client.get_file_content_response("sys", user_prompt)
        
        assert "multiple" in str(e.value).lower()

def test_strip_markdown_prefix_no_code_block(openai_key):
    """
    Test _strip_markdown_prefix returns original text if no code block pattern is found.
    """
    client = OpenAIClient()
    text_without_code_block = "This is a plain text without any code block."

    result = client._strip_markdown_prefix(text_without_code_block)

    # It should return the original text since no code block markers were detected.
    assert result == text_without_code_block

def test_file_content_response_empty_after_stripping(openai_key):
    """
    Test get_file_content_response raises LLMContentFormatError if stripping results in empty content.
    """
    mock_response = MagicMock()
    # The block content is empty or just whitespace which should trigger the exception.
    mock_response.choices[0].message.content = "```python\n\n```"

    with patch("openai.chat.completions.create", return_value=mock_response):
        client = OpenAIClient()
        user_prompt = "Provide the content of an empty Python file."

        with pytest.raises(LLMContentFormatError) as e:
            client.get_file_content_response("sys", user_prompt)
        
        assert "stripped" in str(e.value).lower()


def test_delegation_via_getattr(openai_key):
    ai = AIClient()
    assert hasattr(ai, "get_raw_response")
