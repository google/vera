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
from typing import TYPE_CHECKING, Any, Self, override
from unittest.mock import patch

import pytest
from anyio import Path

from vera import CONFIG
from vera.core.configuration import VeraConfig
from vera.core.data_models.csv import CsvRow, ScoreRange
from vera.core.write_results_to_file import (
    create_report_file,
    get_report_dir,
    write_to_file,
)
from vera.project_name import PROJECT_NAME

if TYPE_CHECKING:
    import pathlib

    from pytest_mock import MockerFixture

from pydantic import ConfigDict


class MockRow(CsvRow):
    model_config = ConfigDict(populate_by_name=True)
    name: str
    score: float

    @override
    def calculate_final_score(self) -> float:
        return self.score

    @property
    @override
    def score_range(self) -> ScoreRange:
        return ScoreRange(min=0, max=1)

    @classmethod
    @override
    def from_columns(cls, **kwargs: Any) -> Self:  # ty:ignore[invalid-method-override]
        return cls(**kwargs)


@pytest.mark.anyio
async def test_get_report_dir_from_config(tmp_path: pathlib.Path) -> None:
    env_dir = tmp_path / "env_dir"
    env_dir.mkdir()
    config = VeraConfig(dst_dir=env_dir)
    with patch(f"{PROJECT_NAME}.core.write_results_to_file.CONFIG", config):
        report_dir = await get_report_dir()
        assert str(report_dir) == str(env_dir.resolve())


@pytest.mark.anyio
async def test_create_report_file(tmp_path: pathlib.Path, mocker: MockerFixture) -> None:
    report_dir = Path(str(tmp_path))
    mocker.patch.object(CONFIG, "report_name", "report")

    file1 = await create_report_file(report_dir)
    assert file1.name == "report_1.csv"
    assert await file1.exists()

    file2 = await create_report_file(report_dir)
    assert file2.name == "report_2.csv"
    assert await file2.exists()


@pytest.mark.anyio
async def test_create_report_file_custom_name(tmp_path: pathlib.Path) -> None:
    report_dir = Path(str(tmp_path))
    config = VeraConfig(report_name="my_custom_report")

    with patch(f"{PROJECT_NAME}.core.write_results_to_file.CONFIG", config):
        file1 = await create_report_file(report_dir)
        assert file1.name == "my_custom_report_1.csv"
        assert await file1.exists()

        file2 = await create_report_file(report_dir)
        assert file2.name == "my_custom_report_2.csv"
        assert await file2.exists()


@pytest.mark.anyio
async def test_write_to_file(tmp_path: pathlib.Path) -> None:
    report_dir = tmp_path / "reports"
    config = VeraConfig(dst_dir=report_dir)
    with patch(f"{PROJECT_NAME}.core.write_results_to_file.CONFIG", config):
        rows = [
            MockRow(identifier=1, name="test1", score=0.8, final_score=0.8),
            MockRow(identifier=2, name="test2", score=0.9, final_score=0.9),
        ]
        await write_to_file(rows)

        report_file = report_dir / "report_1.csv"
        assert report_file.exists()

        content = report_file.read_text()
        assert "test1" in content
        assert "0.8" in content
        assert "test2" in content
        assert "0.9" in content
        assert "Final Score" in content
