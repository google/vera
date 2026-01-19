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

from pathlib import Path
from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from vera.core.configuration import VeraConfig
from vera.main import app


class TestConfig:
    runner = CliRunner()

    def test_config_report_name(self) -> None:
        with (
            patch("vera.config.typer_app.VeraConfig.load") as mock_load,
            # We don't need to patch save if we check the mock instance
        ):
            mock_config = MagicMock(spec=VeraConfig)
            mock_config.report_name = "report"
            mock_load.return_value = mock_config

            # Test setting report name
            result = self.runner.invoke(app, ["config", "--report-name", "custom_report"])
            assert result.exit_code == 0
            assert mock_config.report_name == "custom_report"
            mock_config.save.assert_called_once()
            assert "Report name set to: custom_report" in result.output

    def test_config_display_report_name(self) -> None:
        with (
            patch("vera.config.typer_app.VeraConfig.load") as mock_load,
            patch("vera.config.typer_app.get_config_path") as mock_path,
        ):
            mock_config = MagicMock(spec=VeraConfig)
            mock_config.report_name = "my_report"
            mock_config.dst_dir = Path("/temp")
            mock_config.gemini_api_key = "key"
            mock_config.enable_csv_report = True
            mock_config.log_level = "INFO"
            mock_load.return_value = mock_config

            mock_path_obj = MagicMock(spec=Path)
            mock_path.return_value = mock_path_obj
            mock_path_obj.exists.return_value = True

            # Test displaying config
            result = self.runner.invoke(app, ["config"])
            assert result.exit_code == 0
            assert "Report Name: my_report" in result.output
