# Installation and Usage

This guide covers how to set up Vera and use its command-line interface.

## Prerequisites

- **Python 3.14+**
- [uv](https://github.com/astral-sh/uv) (recommended for package management)
- A **Gemini API Key**

## Installation & Setup

### 1. Create a virtual environment

We recommend using `uv` for a fast and reliable environment setup.

```shell
# Create a virtual environment with Python 3.14
uv venv --python 3.14
source .venv/bin/activate
```

### 2. Install Vera

Install the Vera engine in editable mode.

```shell
uv pip install path/to/vera
```

### 3. Install a Plugin

Vera requires plugins to test specific features. You can install the provided SQL Query
Assistant
example.

```shell
uv pip install plugin_example/sql_query_assistant
```

## Quick Start

Follow these steps to run your first test:

1. **Configure your API Key**:
   ```shell
   vera config -k
   ```
   (You will be prompted to enter your Gemini API key securely)

2. **Verify Plugin Installation**:
   ```shell
   vera list
   ```
   You should see `sql_query_assistant` in the list.

3. **Run Evaluation**:
   ```shell
   # Run the test and save results to the './out' directory
   vera test --dst-dir ./out --runs-count 1
   ```

## CLI Reference

### `vera list`

Lists all registered plugins currently installed and recognized by the system via entry points.

### `vera test`

Evaluates installed features using the registered plugins.

**Options:**

- `-t, --test-tag TEXT`: Only run tests that contain the specified tags. Can be used multiple times.
- `-d, --dst-dir PATH`: The destination directory where the result CSV files will be written.
  Defaults to the configured destination directory or the home directory.
- `-r, --runs-count INTEGER`: The number of times to run the test suite. Useful for testing LLM
  consistency. Defaults to 1.
- `--create-csv`: Enable/Disable the default CSV report generation.
- `-v, --verbose`: Enable verbose output (DEBUG level logs and file paths).
- `-q, --quiet`: Only print error logs.

### `vera config`

Configures Vera default settings persistently.

**Options:**

- `-d, --dst-dir PATH`: The default destination directory for results.
- `-k, --gemini-api-key TEXT`: Set the Gemini API key securely.
- `--disable-csv / --enable-csv`: Toggle default CSV report generation.
- `-l, --log-level TEXT`: Set the default log level (DEBUG, INFO, etc.).

### `vera create`

Scaffolds a new plugin template.

**Options:**

- `--name TEXT` (Required): Name of the feature/plugin (e.g., "my_feature").
- `--description TEXT`: A short description.
- `--plugins-dir PATH`: Where to create the plugin. Defaults to `./vera_plugins`.
- `--override-existing`: Overwrite existing directory if it exists.
