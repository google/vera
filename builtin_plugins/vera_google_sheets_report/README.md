# Google Sheets Report Plugin for Vera

## Overview

This plugin extends `vera` to support publishing test results directly to Google Sheets. It
allows for multi-run reporting, with options to either keep runs in separate sheets or combine them
into a single summary sheet.

## Features

- **Automatic Sheet Management**: Automatically creates new sheets (e.g., "Run 1", "Run 2") if they
  don't exist.
- **Combined Results**: Option to merge multiple test runs into a single "Combined Results"
  sheet.
- **Secure Configuration**: Supports Google Service Account credentials and secure password entry.
- **Seamless Integration**: Hooks directly into `vera test` and `vera config`.

## Installation

Ensure the plugin is installed in your environment:

```bash
pip install builting_plugins/google_sheets_report
```

## Configuration

### 1. Google Cloud Setup

1. Go to the [Google Cloud Console](https://console.cloud.google.com/).
2. Create a new project (or use an existing one).
3. Enable the **Google Sheets API**.
4. Create a **Service Account**:
    - Go to **IAM & Admin > Service Accounts**.
    - Create a service account and grant it necessary permissions (though API access is usually
      sufficient).
    - Create a **Key** in JSON format and download it.
5. **Share the Spreadsheet**: Open the Google Sheet you want to use and share it with the service
   account's email address (found in the JSON file) as an **Editor**.

### 2. Vera Plugin Configuration

Use the `vera config` command to store your credentials and spreadsheet ID:

```bash
# Configure mandatory settings
vera config --gs-spreadsheet-id "your-spreadsheet-id" --gs-credentials "/path/to/your-credentials.json"

# (Optional) Configure user tracking
vera config --gs-user "your_name" --gs-password
```

*If you use `--gs-password` without a value, you will be prompted to enter it securely.*

To verify your configuration:

```bash
vera config
```

## Usage

### Publishing Results

When you run `vera test`, the results are automatically appended to your Google Sheet.

#### Multi-Run Handling

- **Default**: Each run is placed in its own sheet (e.g., "Run 1", "Run 2").
- **Combined**: Use the `--gs-combine` flag to append all results to a single "Combined Results"
  sheet.

```bash
# Run test and combine all suites into one sheet
vera test --gs-combine
```

### Plugin-Specific Help

You can access help for Google Sheets specific arguments by using the `--gs-help` flag:

```bash
# Show eval-specific GS options
vera test --gs-help

# Show config-specific GS options
vera config --gs-help
```

## Data Mapping

The plugin maps your test data (CSV rows) directly to spreadsheet columns. The first row of
the sheet (or the first run in combined mode) will include headers. Subsequent runs in combined mode
will append data rows only.
