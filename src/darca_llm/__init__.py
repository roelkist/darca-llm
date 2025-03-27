"""
darca-llm

Modular, backend-agnostic interface for interacting with large language
models (LLMs).
Default backend: OpenAI

Exports:
    - AIClient: Unified interface for LLM usage
    - BaseLLMClient: Abstract base for all backends
    - OpenAIClient: Concrete backend using OpenAI API
    - All custom exceptions
"""

from .llm import (
    AIClient,
    BaseLLMClient,
    LLMAPIKeyMissing,
    LLMContentFormatError,
    LLMException,
    LLMResponseError,
    OpenAIClient,
)

__all__ = [
    "AIClient",
    "BaseLLMClient",
    "OpenAIClient",
    "LLMException",
    "LLMAPIKeyMissing",
    "LLMResponseError",
    "LLMContentFormatError",
]
