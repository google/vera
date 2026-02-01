# Vera – AI Feature Testing Engine

![Vera Logo](/docs/resources/vera_logo.png)

**Vera
** is an extensible testing engine designed to bring software engineering rigor to AI feature development. It provides a standardized framework for evaluating Generative AI outputs using a
**Hybrid Evaluation
** approach: combining deterministic static checks with semantic "LLM-as-a-Judge" evaluation.

## Why Vera?

Building reliable AI features is hard. Traditional unit tests struggle with the probabilistic nature of LLMs, while manual testing is unscalable and subjective. Vera bridges this gap.

- **🤖 Hybrid Evaluation
  **: strict programmatic validation (e.g., "is valid JSON?") combined with nuanced AI grading (e.g., "is the tone professional?").
- **📏 Spec-Driven Quality
  **: Define success using natural language Rubrics, Safety Constraints, and Golden Datasets that the LLM Judge follows.
- **⚡ High Performance**: Built on `asyncio` and `anyio` for parallel test execution.
- **🔌 Plugin Architecture**: deeply extensible via
  `pluggy`. Add new features, commands, or reporters easily.
- **📊 Standardized Reporting
  **: Get detailed CSV reports with granular scores, reasoning, and pass/fail status.

## Documentation

- **[Installation and Usage](/docs/installation_and_usage.md)**: Setup guide and CLI reference.
- **[Testing Philosophy](/docs/testing_philosophy.md)**: Deep dive into "LLM-as-a-Judge" and Test Specs.
- **[Plugin Development](/docs/plugin_development.md)**: How to build custom evaluation plugins.
- **[Contributing](/docs/contributing.md)**: Guide for contributing to the Vera core engine.

## How It Works

Vera evaluates your AI feature in four steps:

1. **Execution**: Runs your feature against a set of inputs (Test Cases).
2. **Static Analysis**: Runs Python-based checks on the output (e.g., regex, syntax validation).
3. **LLM Evaluation**: An "LLM Judge" (e.g., Gemini) grades the output based on your provided *
   *Specs** (Rubrics, Safety Constraints, Style Guides).
4. **Reporting**: Aggregates all scores and reasoning into a structured report.

## Quick Start

### Prerequisites

- **Python 3.14+**
- **[uv](https://github.com/astral-sh/uv)** (Recommended for dependency management)

### Installation

1. **Set up the environment**:

   ```shell
   # Create a virtual environment with Python 3.14
   uv venv --python 3.14
   source .venv/bin/activate
   ```

2. **Install Vera Core**:

   ```shell
   # Install the core engine from the local directory
   uv pip install vera

   # Or from GitHub
   uv add "git+https://github.com/google/vera.git#subdirectory=vera"
   ```

3. **Install an Example Plugin**:
   Vera requires plugins to define what to test. Let's install the SQL Query Assistant example.

   ```shell
   uv pip install plugin_example/vera_sql_query_assistant
   ```

### Running a Test

1. **Configure API Key**:
   Vera uses Gemini as the default judge. You'll need an API key.

   ```shell
   vera config -k
   # Follow the prompt to enter your key securely
   ```

2. **Verify Setup**:
   Check if the plugin is recognized.

   ```shell
   vera list
   # Should show: vera_sql_query_assistant
   ```

3. **Run the Evaluation**:

   ```shell
   # Run tests and save results to ./out
   vera test --dst-dir ./out
   ```

You can now open the generated CSV file in the `out/` directory to analyze the results.

---
*Maintained by the Vera Team.*
