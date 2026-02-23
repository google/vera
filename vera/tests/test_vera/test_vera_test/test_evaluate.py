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
import asyncio
import contextlib
import math
from typing import Any, Never, Self, override
from unittest.mock import AsyncMock, MagicMock

import pytest
from pydantic import ConfigDict

from vera.core.data_models.csv import CsvColumn, CsvRow, ScoreRange
from vera.core.data_models.test_case import TestCase
from vera.core.data_models.test_case.input import TestCaseInput
from vera.core.data_models.test_case.output import TestCaseOutput
from vera.vtest.vtest import TestingService

from .mock_cli_service import MockCliService


class MockInput(TestCaseInput):
    @override
    def to_description_prompt(self) -> str:
        return ""


class MockOutput(TestCaseOutput):
    @override
    def to_output_description_prompt(self) -> str:
        return ""


class MockRow(CsvRow):
    model_config = ConfigDict(populate_by_name=True)

    @override
    def calculate_final_score(self) -> float:
        return 1.0

    @property
    @override
    def score_range(self) -> ScoreRange:
        return ScoreRange(min=0, max=1)

    @classmethod
    @override
    def from_columns(
        cls,
        test_case: TestCase,
        test_output: TestCaseOutput,
        llm_checks_columns: CsvColumn,
        static_checks_columns: CsvColumn,
    ) -> Self:
        return cls.model_validate({"Test Case ID": test_case.id, "Final Score": 1.0})


class MockColumn(CsvColumn):
    pass


@pytest.mark.anyio
async def test_evaluation_service_evaluate() -> None:
    test_case = TestCase(id=1, name="N", description="D", input=MockInput())  # ty:ignore[missing-argument]
    plugin_service = MagicMock()
    plugin_service.get_resources_dir.return_value = MagicMock()
    plugin_service.run_feature = AsyncMock(return_value=MockOutput())
    plugin_service.run_static_tests = MagicMock(return_value=MockColumn())
    plugin_service.llm_evaluation = AsyncMock(return_value=MockColumn())
    plugin_service.get_csv_row_class.return_value = MockRow
    plugin_service.publish_results = MagicMock(return_value=[AsyncMock()])

    cli_service = MockCliService()
    es = TestingService(
        test_cases=[test_case],
        plugin_service=plugin_service,
        cli_service=cli_service,
    )

    await es.run_tests()
    assert len(es.csv_rows) == 1
    assert math.isclose(es.csv_rows[0].final_score, 1.0, abs_tol=0.001)
    assert math.isclose(cli_service.overall_advances, 1.0, abs_tol=0.001)


@pytest.mark.anyio
async def test_evaluation_service_timeout() -> None:
    test_case = TestCase(id=1, name="N", description="D", input=MockInput())  # ty:ignore[missing-argument]
    test_case.config.timeout_seconds = 0.01  # ty:ignore[invalid-assignment]

    plugin_service = MagicMock()

    async def slow_run(*_: Any, resources_dir: Any) -> Any:  # noqa: ANN401
        await asyncio.sleep(0.1)
        return MockOutput()

    plugin_service.run_feature = slow_run

    ts = TestingService(
        test_cases=[test_case],
        plugin_service=plugin_service,
        cli_service=MockCliService(),
    )

    # It should log the exception and not raise it unless strict_mode is True
    await ts.run_tests()
    assert len(ts.csv_rows) == 0


@pytest.mark.anyio
async def test_non_strict_failure_does_not_block() -> None:
    tc1 = TestCase(id=1, name="TC1", description="D", input=MockInput())  # ty:ignore[missing-argument]
    tc2 = TestCase(id=2, name="TC2", description="D", input=MockInput())  # ty:ignore[missing-argument]
    tc3 = TestCase(id=3, name="TC3", description="D", input=MockInput())  # ty:ignore[missing-argument]

    # TC2 will fail
    async def run_feature(test_case: Any, resources_dir: Any) -> MockOutput:  # noqa: ANN401, RUF029
        if test_case.id == 2:
            msg = "Failure"
            raise ValueError(msg)
        return MockOutput()

    plugin_service = MagicMock()
    plugin_service.get_resources_dir.return_value = MagicMock()
    plugin_service.run_feature = run_feature
    plugin_service.run_static_tests = MagicMock(return_value=MockColumn())
    plugin_service.llm_evaluation = AsyncMock(return_value=MockColumn())
    plugin_service.get_csv_row_class.return_value = MockRow

    ts = TestingService([tc1, tc2, tc3], plugin_service, MockCliService())
    await ts.run_tests()

    # TC1 and TC3 should be in csv_rows
    assert len(ts.csv_rows) == 2


@pytest.mark.anyio
async def test_publish_results_called_even_on_strict_failure() -> None:
    tc1 = TestCase(id=1, name="TC1", description="D", input=MockInput())  # ty:ignore[missing-argument]
    tc1.config.strict_mode = True

    async def run_feature(test_case: Any, resources_dir: Any) -> Never:  # noqa: ANN401, RUF029
        msg = "Failure"
        raise ValueError(msg)

    plugin_service = MagicMock()
    plugin_service.get_resources_dir.return_value = MagicMock()
    plugin_service.run_feature = run_feature
    plugin_service.publish_results.return_value = [AsyncMock()()]
    plugin_service.get_csv_row_class.return_value = MockRow

    ts = TestingService([tc1], plugin_service, MockCliService())

    with contextlib.suppress(Exception):
        await ts.run_tests()

    await ts.publish_results(0)

    plugin_service.publish_results.assert_called_once()


@pytest.mark.anyio
async def test_evaluation_service_strict_mode_error() -> None:
    test_case = TestCase(id=1, name="N", description="D", input=MockInput())  # ty:ignore[missing-argument]
    test_case.config.strict_mode = True
    test_case.config.timeout_seconds = 0.01  # ty:ignore[invalid-assignment]

    plugin_service = MagicMock()

    async def slow_run(*_: Any, resources_dir: Any) -> Any:  # noqa: ANN401
        await asyncio.sleep(0.1)
        return MockOutput()

    plugin_service.run_feature = slow_run

    ts = TestingService(
        test_cases=[test_case],
        plugin_service=plugin_service,
        cli_service=MockCliService(),
    )

    with contextlib.suppress(Exception):
        await ts.run_tests()

    assert len(ts.csv_rows) == 0
