# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

import pytest
from vera.core.configuration import CONFIG
from vera_google_sheets_report.plugin_impl import (
    display_config_command_help,
    display_test_command_help,
    handle_config_command_display,
    handle_config_command_extra_args,
    handle_test_command_extra_args,
    publish_results,
)

if TYPE_CHECKING:
    from _pytest.capture import CaptureFixture


def test_handle_test_command_extra_args() -> None:
    handle_test_command_extra_args(["--gs-combine"])
    assert CONFIG.gs_combine is True
    handle_test_command_extra_args([])
    assert CONFIG.gs_combine is False


def test_display_test_command_help(capsys: CaptureFixture[str]) -> None:
    args = ["--gs-help"]
    display_test_command_help(args)
    captured = capsys.readouterr()
    assert "Google Sheets Report 'eval' options:" in captured.out
    assert "--gs-combine" in captured.out
    assert "--gs-help" not in args


def test_handle_config_command_extra_args() -> None:
    config: MagicMock = MagicMock()
    config.as_type.return_value = config
    sheet_id: str = "123"
    creds_file: str = "creds.json"
    user = "test-user"
    password = "test-password"  # noqa: S105
    handle_config_command_extra_args(
        config,
        [
            "--gs-credentials",
            creds_file,
            "--gs-spreadsheet-id",
            sheet_id,
            "--gs-user",
            user,
            "--gs-password",
            password,
        ],
    )
    assert config.gs_credentials == creds_file
    assert config.gs_spreadsheet_id == sheet_id
    assert config.gs_user == user
    assert config.gs_password == password


@patch("getpass.getpass")
def test_handle_config_command_password_prompt(mock_getpass: MagicMock) -> None:
    config: MagicMock = MagicMock()
    config.as_type.return_value = config
    mock_getpass.return_value = "secret"
    handle_config_command_extra_args(config, ["--gs-password"])
    mock_getpass.assert_called_once()
    assert config.gs_password == "secret"  # noqa: S105


def test_display_config_command_help(capsys: CaptureFixture[str]) -> None:
    args = ["--gs-help"]
    display_config_command_help(args)
    captured = capsys.readouterr()
    assert "Google Sheets Report 'config' options:" in captured.out
    assert "--gs-credentials" in captured.out
    assert "--gs-password" in captured.out
    assert "--gs-help" not in args


@patch("vera_google_sheets_report.plugin_impl.logger")
def test_handle_config_command_display(mock_logger: MagicMock) -> None:
    config = MagicMock()
    config.as_type.return_value = config
    config.gs_spreadsheet_id = "id123"
    config.gs_credentials = "path/to/json"
    config.gs_user = "bob"
    config.gs_password = "password123"  # noqa: S105

    handle_config_command_display(config)

    # Check that the password is masked
    mock_logger.info.assert_any_call("  GS Password: %s", "*******")
    mock_logger.info.assert_any_call("  GS Spreadsheet ID: %s", "id123")
    mock_logger.info.assert_any_call("  GS User: %s", "bob")


@pytest.mark.asyncio
@patch("vera_google_sheets_report.plugin_impl.GoogleSheetsClient")
async def test_publish_results_no_combine(mock_client_class: MagicMock) -> None:
    mock_client = mock_client_class.return_value
    sheet_id: str = "123"
    creds_file: str = "creds.json"
    CONFIG.gs_credentials = creds_file
    CONFIG.gs_spreadsheet_id = sheet_id
    CONFIG.gs_combine = False

    row = MagicMock()
    row.model_dump.return_value = {"Header1": "Value1"}
    rows = [row]

    await publish_results(rows, run_index=0)

    mock_client_class.assert_called_once_with(creds_file)
    mock_client.ensure_sheet_exists.assert_called_once_with(sheet_id, "Run 1")
    mock_client.append_rows.assert_called_once_with(
        sheet_id, "'Run 1'!A1", [["Header1"], ["Value1"]]
    )


@pytest.mark.asyncio
@patch("vera_google_sheets_report.plugin_impl.GoogleSheetsClient")
async def test_publish_results_combine(mock_client_class: MagicMock) -> None:
    mock_client = mock_client_class.return_value
    sheet_id: str = "123"
    creds_file: str = "creds.json"
    CONFIG.gs_credentials = creds_file
    CONFIG.gs_spreadsheet_id = sheet_id
    CONFIG.gs_combine = True

    row = MagicMock()
    row.model_dump.return_value = {"Header1": "Value1"}
    rows = [row]

    # Run 0 should have header
    await publish_results(rows, run_index=0)
    mock_client.append_rows.assert_called_with(
        sheet_id, "'Combined Results'!A1", [["Header1"], ["Value1"]]
    )

    # Run 1 should NOT have a header
    await publish_results(rows, run_index=1)
    mock_client.append_rows.assert_called_with(sheet_id, "'Combined Results'!A1", [["Value1"]])
