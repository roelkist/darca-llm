API Reference
=============

This section documents the darca-llm API.

---

AIClient
--------

.. autofunction:: darca_llm.AIClient

    Unified interface to interact with LLMs.

    :param backend: The backend to use (default: "openai")
    :raises LLMException: If the backend is unsupported

---

OpenAIClient
------------

.. autofunction:: darca_llm.OpenAIClient

    Handles direct interaction with OpenAI's API.
    Inherits from `BaseLLMClient`.

---

BaseLLMClient
-------------

.. autofunction:: darca_llm.BaseLLMClient

    Abstract base class for all LLM clients.

    Methods:
        - `get_raw_response(system, user, ...)`
        - `get_file_content_response(system, file_content, ...)`

---

Exceptions
----------

.. autofunction:: darca_llm.LLMException
.. autofunction:: darca_llm.LLMAPIKeyMissing
.. autofunction:: darca_llm.LLMContentFormatError
.. autofunction:: darca_llm.LLMResponseError

