API Reference
=============

This section documents the darca-llm API.

---

AIClient
--------

.. autoclass:: darca_llm.AIClient
   :members:
   :show-inheritance:

   Unified interface to interact with LLMs.

   :param backend: The backend to use (default: "openai")
   :raises LLMException: If the backend is unsupported

---

OpenAIClient
------------

.. autoclass:: darca_llm.OpenAIClient
   :members:
   :show-inheritance:

   Handles direct interaction with OpenAI's API.
   Inherits from :class:`BaseLLMClient`.

---

BaseLLMClient
-------------

.. autoclass:: darca_llm.BaseLLMClient
   :members:
   :show-inheritance:
   :undoc-members:

   Abstract base class for all LLM clients.

   Methods:
       - ``get_raw_response(system, user, ...)``
       - ``get_file_content_response(system, file_content, ...)``

---

Exceptions
----------

.. autoclass:: darca_llm.LLMException
   :show-inheritance:

.. autoclass:: darca_llm.LLMAPIKeyMissing
   :show-inheritance:

.. autoclass:: darca_llm.LLMContentFormatError
   :show-inheritance:

.. autoclass:: darca_llm.LLMResponseError
   :show-inheritance:
