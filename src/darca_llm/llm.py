import os
import re
from abc import ABC, abstractmethod

import openai
from darca_exception.exception import DarcaException
from darca_log_facility.logger import DarcaLogger

# === Custom Exceptions ===


class LLMException(DarcaException):
    """Base class for all darca-llm exceptions."""


class LLMAPIKeyMissing(LLMException):
    """Raised when the API key is missing for the selected LLM provider."""


class LLMResponseError(LLMException):
    """Raised when an LLM API request fails or returns malformed data."""


class LLMContentFormatError(LLMException):
    """Raised when the input content contains multiple code blocks."""


# === Abstract Base Client ===


class BaseLLMClient(ABC):
    """
    Abstract base class for LLM backends. Provides shared logic for file
    content processing.
    """

    @abstractmethod
    def get_raw_response(
        self,
        system: str,
        user: str,
        llm: str = "gpt-4",
        temperature: float = 1.0,
    ) -> str:
        """
        Send a raw prompt (system + user) to the LLM and return the response.
        """
        pass

    def get_file_content_response(
        self,
        system: str,
        file_content: str,
        llm: str = "gpt-4",
        temperature: float = 1.0,
    ) -> str:
        """
        Process a prompt that includes the content of a single file.
        Cleans markdown/code formatting and ensures only one block is present.
        """
        if not self._has_single_block(file_content):
            raise LLMContentFormatError(
                message="Expected a single file block, but found multiple.",
                error_code="LLM_CONTENT_MULTIBLOCK",
                metadata={"content_preview": file_content[:100]},
            )
        cleaned = self._strip_markdown_prefix(file_content)
        return self.get_raw_response(system, cleaned, llm, temperature)

    def _strip_markdown_prefix(self, text: str) -> str:
        """
        Strip markdown/code block prefix such as '''yaml or ```python.
        """
        pattern = r"^(?:(\"\"\"|```)[a-zA-Z]+\s*)"
        return re.sub(pattern, "", text.strip())

    def _has_single_block(self, text: str) -> bool:
        """
        Ensure content includes only a single markdown/code block.
        """
        triple_quote_blocks = len(re.findall(r'"""[a-zA-Z]*', text))
        triple_backtick_blocks = len(re.findall(r"```[a-zA-Z]*", text))
        return (triple_quote_blocks + triple_backtick_blocks) <= 1


# === OpenAI Implementation ===


class OpenAIClient(BaseLLMClient):
    """
    LLM backend that uses OpenAI's GPT models via their official API.
    """

    def __init__(self):
        self.logger = DarcaLogger("darca-llm").get_logger()
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise LLMAPIKeyMissing(
                message="OPENAI_API_KEY environment variable is not set.",
                error_code="LLM_API_KEY_MISSING",
                metadata={"provider": "openai"},
            )
        openai.api_key = api_key

    def get_raw_response(
        self,
        system: str,
        user: str,
        llm: str = "gpt-4",
        temperature: float = 1.0,
    ) -> str:
        """
        Send system + user prompt to OpenAI and return the chat response.
        """
        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ]
        try:
            self.logger.debug("Sending prompt to OpenAI", extra={"model": llm})
            response = openai.chat.completions.create(
                model=llm, messages=messages, temperature=temperature
            )
            content = response.choices[0].message.content
            self.logger.debug("Received response from OpenAI")
            return content

        except openai.OpenAIError as oe:
            raise LLMResponseError(
                message="OpenAI API returned an error.",
                error_code="LLM_API_REQUEST_FAILED",
                metadata={
                    "model": llm,
                    "temperature": temperature,
                    "prompt_preview": user[:100],
                    "system_prompt_preview": system[:100],
                },
                cause=oe,
            )

        except Exception as e:
            raise LLMResponseError(
                message="Unexpected failure during OpenAI response parsing.",
                error_code="LLM_RESPONSE_PARSE_ERROR",
                metadata={"model": llm, "temperature": temperature},
                cause=e,
            )


# === AIClient Wrapper ===


class AIClient:
    """
    A unified client for interacting with LLMs using the darca pluggable
    backend system.
    Defaults to OpenAI.
    """

    def __init__(self, backend: str = "openai"):
        """
        Initialize the AIClient with the given backend.
        """
        if backend == "openai":
            self._client = OpenAIClient()
        else:
            raise LLMException(
                message=f"LLM backend '{backend}' is not supported.",
                error_code="LLM_UNSUPPORTED_BACKEND",
                metadata={"requested_backend": backend},
            )

    def __getattr__(self, name):
        """
        Delegate calls to the selected backend client.
        """
        return getattr(self._client, name)
