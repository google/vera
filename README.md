# Vera – Your AI Feature Evaluation Tool

![Vera Logo](/docs/resources/vera_logo.png)

Vera is an extensible engine designed to evaluate AI features through a combination of static checks
and "LLM-as-a-Judge" evaluations. It provides a standardized way to test AI outputs against
predefined rubrics, safety constraints, and golden datasets.

## Documentation

- **[Installation and Setup](/docs/installation_and_usage.md)**: How to get Vera running on your
  machine.
- **[Testing Philosophy](/docs/testing_philosophy.md)**: The "Why" behind Vera and how it uses
  LLM Judges.
- **[Plugin Development](/docs/plugin_development.md)**: A guide for developers on how to create
  custom evaluation plugins.
- **[Contributing](/docs/CONTRIBUTING.md)**: How to contribute to the core Vera engine.

## Core Capabilities

- **Plugin-based Architecture**: Add support for different features by creating custom plugins using
  `pluggy`.
- **Asynchronous Execution**: Run multiple test cases in parallel for fast evaluation using
  `asyncio` and `anyio`.
- **Multi-layered Evaluation**: Programmatic static checks combined with high-reasoning LLM Judges.
- **Standardized Reporting**: Generates comprehensive CSV reports with detailed scores and
  reasoning.
- **Concurrent Runs**: Support for running the entire test suite multiple times to detect variance.

## Quick Start

If uv is not installed

```shell
curl -LsSf https://astral.sh/uv/install.sh | sh
```

If it is installed make sure to use the latest version

```shell
uv self update  # or `pip3 install --upgrade uv`
```

Then install vera, the example plugin and run the test cases:

```shell
# 1. Install Vera and the example plugin
uv venv --python 3.14
uv pip install vera plugin_example/sql_query_assistant
vera list

# 2. Configure Gemini API Key and destination directory
vera config -k
vera config -d ./out

# 3. Run the example evaluation
vera test
```

You can always use `vera {command} --help` to see all available options as well as `vera --help`.
