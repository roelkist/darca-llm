import os
import re
from abc import ABC, abstractmethod

import openai
from darca_exception.exception import DarcaException
from darca_log_facility.logger import DarcaLogger

# === Custom Exceptions ===


class LLMException(DarcaException):
    """
    Base class for all darca-llm exceptions.

    Inherits from :class:`DarcaException`.
    """


class LLMAPIKeyMissing(LLMException):
    """
    Raised when the API key is missing for the selected LLM provider.

    This exception indicates that the environment variable for the API key
    (e.g., ``OPENAI_API_KEY``) is not set, preventing the LLM from being used.
    """


class LLMResponseError(LLMException):
    """
    Raised when an LLM API request fails or returns malformed data.

    This exception can be raised due to API connectivity issues, invalid
    responses, or unexpected errors from the LLM provider.
    """


class LLMContentFormatError(LLMException):
    """
    Raised when the input content contains multiple code blocks or
    when the response cannot be properly stripped of Markdown/code block
    formatting.

    This exception is specifically tailored to ensure that the LLM response
    includes exactly one code block and that the format matches the expected
    structure.
    """


# === Abstract Base Client ===


class BaseLLMClient(ABC):
    """
    Abstract base class for LLM backends. Provides shared logic for file
    content processing.

    Concrete implementations must implement the :meth:`get_raw_response`
    method, which handles sending prompts to the respective LLM.
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
        Send a raw prompt (consisting of a system message and a user message)
        to the LLM and return the string response.

        :param system: The system-level instructions or context for the LLM.
        :type system: str
        :param user: The user-level query or request for the LLM.
        :type user: str
        :param llm: The identifier for the LLM model to use (e.g., ``gpt-4``).
        :type llm: str
        :param temperature: The sampling temperature for the LLM, controlling
            creativity in the response.
        :type temperature: float
        :return: The raw response text returned by the LLM.
        :rtype: str
        :raises LLMResponseError: If the LLM request fails or returns an
                                  invalid response.
        :raises LLMAPIKeyMissing: If the required API key is not set in
                                  the environment.
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

        This method:

        1. Sends the prompt to the LLM via :meth:`get_raw_response`.
        2. Verifies that the returned response contains exactly one code block.
        3. Strips any Markdown or code block formatting from the response.

        :param system: The system message for the LLM.
        :type system: str
        :param user: The user query or request for the LLM, typically
                     referencing a file content request.
        :type user: str
        :param llm: The identifier for the LLM model to use
                    (e.g., ``gpt-4``).
        :type llm: str
        :param temperature: The sampling temperature for the LLM, controlling
            creativity in the response.
        :type temperature: float
        :return: Cleaned-up text containing the single file content.
        :rtype: str
        :raises LLMContentFormatError: If the response has multiple
            code blocks, or if it cannot be properly stripped of
            Markdown/code formatting.
        """
        response = self.get_raw_response(system, user, llm, temperature)

        if not self._has_single_block(response):
            raise LLMContentFormatError(
                message=(
                    "Expected a single file block in the response, "
                    "but found multiple."
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
        Strip Markdown or code block prefix and suffix
        (e.g., `````python ... ```).

        This method uses a regular expression to detect code blocks
        delimited by
        triple backticks. If a match is found, it returns only the
        content within
        the code block, otherwise returns the original text stripped of
        leading/trailing whitespace.

        :param text: The text potentially containing Markdown or code
          block formatting.
        :type text: str
        :return: The stripped text without the code block delimiters.
        :rtype: str
        """
        pattern = r"^```(?:[\w+-]*)\n([\s\S]*?)\n```$"
        match = re.match(pattern, text.strip())

        if match:
            return match.group(
                1
            ).strip()  # Return only the content within the block
        return (
            text.strip()
        )  # Return the original text if it doesn't match the pattern

    def _has_single_block(self, text: str) -> bool:
        """
        Check if the text contains exactly one Markdown/code block.

        :param text: The text that may contain zero, one, or multiple
          code blocks.
        :type text: str
        :return: True if there is exactly one code block in the text,
          False otherwise.
        :rtype: bool
        """
        blocks = re.findall(r"```(?:[\w+-]*)\n[\s\S]*?\n```", text)
        return len(blocks) == 1


# === OpenAI Implementation ===


class OpenAIClient(BaseLLMClient):
    """
    LLM backend that uses OpenAI's GPT models via their official API.

    This class implements the :class:`BaseLLMClient` interface, utilizing
    the OpenAI Python client library to make requests to GPT models
    (e.g., ``gpt-4``, ``gpt-3.5-turbo``).
    """

    def __init__(self):
        """
        Initialize the OpenAI client.

        :raises LLMAPIKeyMissing: If the ``OPENAI_API_KEY`` environment
          variable is not set.
        """
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
        Send a system and user prompt to OpenAI and return the chat response.

        :param system: The system message providing context or instructions
          to the LLM.
        :type system: str
        :param user: The user message, typically containing the main query.
        :type user: str
        :param llm: The identifier of the OpenAI model to
          use (e.g., ``gpt-4``).
        :type llm: str
        :param temperature: Sampling temperature for the request to control
          response randomness.
        :type temperature: float
        :return: The text content of the LLM response.
        :rtype: str
        :raises LLMResponseError: If the API request fails or the response
          cannot be parsed.
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
    backend system. Defaults to the OpenAI backend.

    This class acts as a simple wrapper, delegating all method calls
    to the selected backend. Currently, only ``openai`` is supported.
    """

    def __init__(self, backend: str = "openai"):
        """
        Initialize the AIClient with the given backend.

        :param backend: The chosen LLM backend. Currently only ``openai``
          is supported.
        :type backend: str
        :raises LLMException: If the requested backend is not supported.
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
        Delegate attribute or method calls to the selected backend client.

        If this client does not have the attribute or method, it is fetched
        from the underlying backend (e.g., :class:`OpenAIClient`).

        :param name: The name of the attribute or method to be accessed.
        :type name: str
        :return: The attribute or method from the underlying backend client.
        """
        return getattr(self._client, name)
