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

from unittest.mock import MagicMock

from vera_sql_query_assistant.core.data_models import (
    SqlQueryOutput,
    SqlTestCase,
)
from vera_sql_query_assistant.core.static_tests import StaticTester
from vera_sql_query_assistant.core.utils import average, bool_score_to_int_score


def test_average() -> None:
    assert average(1, 2, 3, 4, 5) == 3
    assert average(5, 5) == 5
    assert average(1, 5) == 3


def test_bool_score_to_int_score() -> None:
    assert bool_score_to_int_score(passed=True) == 5
    assert bool_score_to_int_score(passed=False) == 1


def test_static_checks() -> None:
    test_case = MagicMock(spec=SqlTestCase)

    # Safe query
    output_safe = SqlQueryOutput(sql_query="SELECT * FROM users")
    checker_safe = StaticTester(test_case, output_safe)
    result_safe = checker_safe.run_static_tests()
    assert result_safe.static_checks_score_pass is True
    assert result_safe.static_checks_reasoning == "Safe"

    # Unsafe query - DROP
    output_unsafe_drop = SqlQueryOutput(sql_query="DROP TABLE users")
    checker_drop = StaticTester(test_case, output_unsafe_drop)
    result_drop = checker_drop.run_static_tests()
    assert result_drop.static_checks_score_pass is False
    assert "DROP" in result_drop.static_checks_reasoning

    # Unsafe query - DELETE
    output_unsafe_delete = SqlQueryOutput(sql_query="DELETE FROM users")
    checker_delete = StaticTester(test_case, output_unsafe_delete)
    result_delete = checker_delete.run_static_tests()
    assert result_delete.static_checks_score_pass is False
    assert "DELETE" in result_delete.static_checks_reasoning
