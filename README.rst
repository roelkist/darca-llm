darca-llm
=========

Modular, backend-agnostic interface for interacting with large language models (LLMs).

This library is part of the `darca-*` ecosystem and provides a plug-and-play, extensible interface to communicate with LLM providers like OpenAI. It is designed with testability, structure, and future integration in mind.

|Build Status| |Deploy Status| |CodeCov| |Formatting| |License| |PyPi Version| |Docs|

.. |Build Status| image:: https://github.com/roelkist/darca-llm/actions/workflows/ci.yml/badge.svg
   :target: https://github.com/roelkist/darca-llm/actions
.. |Deploy Status| image:: https://github.com/roelkist/darca-llm/actions/workflows/cd.yml/badge.svg
   :target: https://github.com/roelkist/darca-llm/actions
.. |Codecov| image:: https://codecov.io/gh/roelkist/darca-llm/branch/main/graph/badge.svg
   :target: https://codecov.io/gh/roelkist/darca-llm
   :alt: Codecov
.. |Formatting| image:: https://img.shields.io/badge/code%20style-black-000000.svg
   :target: https://github.com/psf/black
   :alt: Black code style
.. |License| image:: https://img.shields.io/badge/license-MIT-blue.svg
   :target: https://opensource.org/licenses/MIT
.. |PyPi Version| image:: https://img.shields.io/pypi/v/darca-llm
   :target: https://pypi.org/project/darca-llm/
   :alt: PyPi
.. |Docs| image:: https://img.shields.io/github/deployments/roelkist/darca-llm/github-pages
   :target: https://roelkist.github.io/darca-llm/
   :alt: GitHub Pages

---

Features
--------

- ✅ Unified `AIClient` interface for all LLMs
- 🔌 OpenAI integration out of the box (GPT-4, GPT-3.5)
- 🧱 Extensible abstract interface (`BaseLLMClient`) for new providers
- 🧪 Full pytest support with 100% coverage
- 📦 Rich exception handling with structured `DarcaException`
- 📋 Markdown-aware content formatting using `_strip_markdown_prefix`
- 🧠 Logging support via `darca-log-facility`

---

Quickstart
----------

1. Install dependencies:

.. code-block:: bash

    make install

2. Run all quality checks (format, test, docs):

.. code-block:: bash

    make check

3. Run tests only:

.. code-block:: bash

    make test

4. Use the client:

.. code-block:: python

    from darca_llm import AIClient

    ai = AIClient()
    response = ai.get_raw_response(
        system="You are a helpful assistant.",
        user="What is a Python decorator?"
    )
    print(response)

---

Using `get_file_content_response`
----------------------------------

The `get_file_content_response()` method allows for structured file content prompting with LLMs.

Example:

.. code-block:: python

    from darca_llm import AIClient

    client = AIClient()

    user_prompt = "Provide the content of a simple Python file."

    result = client.get_file_content_response(
        system="Explain the code.",
        user=user_prompt
    )
    print(result)

This method ensures that only a single code block is returned and properly stripped of formatting using `_strip_markdown_prefix()`.

---

Error Handling
--------------

All exceptions are subclasses of `DarcaException` and include:

- `LLMException`: Base for all LLM-specific errors
- `LLMAPIKeyMissing`: Raised when the API key is missing for the selected backend
- `LLMContentFormatError`: Raised when:
  - Multiple blocks are detected within the response
  - The response cannot be properly stripped of markdown/code block formatting
- `LLMResponseError`: Raised when the LLM provider returns an error or response parsing fails

All exceptions include:

- `error_code`
- `message`
- Optional `metadata`
- Optional `cause`
- Full stack trace logging

---

Documentation
-------------

Build and view the docs:

.. code-block:: bash

    make docs

Open the HTML documentation at:

::

    docs/build/html/index.html

For detailed usage, refer to the `usage.rst` documentation.

---

