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
        user: str,
        llm: str = "gpt-4",
        temperature: float = 1.0,
    ) -> str:
        """
        Process a prompt to return the content of a single file.
        This method sends the prompt to the LLM, verifies the response contains
        a single code block,
        and strips any markdown or code formatting prefixes.
        """
        response = self.get_raw_response(system, user, llm, temperature)

        if not self._has_single_block(response):
            raise LLMContentFormatError(
                message=(
                    "Expected a single file block in the response,"
                    " but found multiple."
                ),
                error_code="LLM_CONTENT_MULTIBLOCK",
                metadata={"response_preview": response[:100]},
            )

        cleaned_response = self._strip_markdown_prefix(response)

        if not cleaned_response.strip():
            raise LLMContentFormatError(
                message=(
                    "The response could not be properly stripped of "
                    "markdown/code block formatting."
                ),
                error_code="LLM_CONTENT_STRIP_ERROR",
                metadata={"response_preview": response[:100]},
            )

        return cleaned_response

    def _strip_markdown_prefix(self, text: str) -> str:
        """
        Strip markdown/code block prefix and suffix such as ```python ... ```.
        """
        pattern = r"^```(?:[\w+-]*)\n([\s\S]*?)\n```$"
        match = re.match(pattern, text.strip())
        
        if match:
            return match.group(1).strip()  # Return only the content within the block
        return text.strip()  # Return the original text if it doesn't match the pattern

    def _has_single_block(self, text: str) -> bool:
        """
        Ensure content includes only a single markdown/code block.
        """
        # Match blocks that start and end with ```
        blocks = re.findall(r"```(?:[\w+-]*)\n[\s\S]*?\n```", text)
        return len(blocks) == 1


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
