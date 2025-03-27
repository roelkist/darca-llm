Usage
=====

This document explains how to use `darca-llm` in detail.

---

Basic Example
-------------

.. code-block:: python

    from darca_llm import AIClient

    client = AIClient()

    result = client.get_raw_response(
        system="You are a helpful assistant.",
        user="What are list comprehensions in Python?",
    )

    print(result)

---

Backends
--------

Currently supported:

- `OpenAI` (default)

To switch or prepare for future backends:

.. code-block:: python

    AIClient(backend="openai")  # Claude, Mistral, etc., coming soon

---

File Content Prompting
----------------------

`darca-llm` supports file-style content passed directly to the model.

.. code-block:: python

    file_data = '''"""python
    def hello():
        print("Hello!")
    """'''

    result = client.get_file_content_response(
        system="Explain the code.",
        file_content=file_data
    )

This strips markdown/code block formatting and ensures only one code block is included.

Raises `LLMContentFormatError` if multiple blocks are detected.

---

Error Handling
--------------

All exceptions are subclasses of `DarcaException` and include:

- `LLMException`: Base for all LLM-specific errors
- `LLMAPIKeyMissing`: No API key found
- `LLMContentFormatError`: Invalid code block formatting
- `LLMResponseError`: LLM provider returned an error

All exceptions include:

- `error_code`
- `message`
- Optional `metadata`
- Optional `cause`
- Full stack trace logging

---

Logging
-------

This module uses `darca-log-facility` and integrates with `DarcaLogger`.

All API calls and exceptions are logged automatically.

Logs are written to:

- `logs/darca-llm.log`
- Standard console output

---

Command Line Integration
------------------------

Not yet available, but `darca-llm` is CLI-ready. A future CLI module will be built around `AIClient`.

