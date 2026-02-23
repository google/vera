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

from typing import Self, override

from pydantic import ConfigDict

from vera.core.data_models.csv import CsvColumn, CsvRow, ScoreRange
from vera.core.data_models.test_case import TestCase
from vera.core.data_models.test_case.input import TestCaseInput
from vera.core.data_models.test_case.output import TestCaseOutput


class MockInput(TestCaseInput):
    value: str

    @override
    def to_description_prompt(self) -> str:
        return f"Input: {self.value}"


class MockOutput(TestCaseOutput):
    result: str

    @override
    def to_output_description_prompt(self) -> str:
        return f"Output: {self.result}"


class MockLlmColumn(CsvColumn):
    score: int


class MockStaticColumn(CsvColumn):
    passed: bool


class MockRow(CsvRow[MockInput, MockOutput, MockLlmColumn, MockStaticColumn]):
    model_config = ConfigDict(populate_by_name=True)
    score: int
    passed: bool

    @override
    def calculate_final_score(self) -> float:
        return float(self.score) if self.passed else 0.0

    @property
    @override
    def score_range(self) -> ScoreRange:
        return ScoreRange(min=0, max=5)

    @override
    @classmethod
    def from_columns(
        cls,
        test_case: TestCase[MockInput],
        test_output: MockOutput,
        llm_checks_columns: MockLlmColumn,
        static_checks_columns: MockStaticColumn,
    ) -> Self:
        return cls.model_validate({
            "identifier": test_case.id,
            "score": llm_checks_columns.score,
            "passed": static_checks_columns.passed,
            "final_score": float(llm_checks_columns.score) if static_checks_columns.passed else 0.0,
        })


def test_test_case_validation() -> None:
    tc = TestCase(
        id=1,
        name="Test Case 1",
        description="A test",
        input=MockInput(value="input_val"),
    )  # ty:ignore[missing-argument]
    assert tc.id == 1
    assert tc.config.timeout_seconds == 600  # Default value
    assert tc.input.value == "input_val"


def test_test_case_input_prompt() -> None:
    mi = MockInput(value="hello")
    assert mi.to_description_prompt() == "Input: hello"


def test_csv_row_logic() -> None:
    tc = TestCase(id=1, name="Test", description="Desc", input=MockInput(value="val"))  # ty:ignore[missing-argument]
    out = MockOutput(result="res")
    llm_cols = MockLlmColumn(score=5)
    static_cols = MockStaticColumn(passed=True)

    row = MockRow.from_columns(tc, out, llm_cols, static_cols)
    assert row.score == 5
    assert row.passed is True
    assert row.final_score == 5

    static_cols_fail = MockStaticColumn(passed=False)
    row_fail = MockRow.from_columns(tc, out, llm_cols, static_cols_fail)
    assert row_fail.final_score == 0
