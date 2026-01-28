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

from collections import defaultdict
from typing import TYPE_CHECKING, Any

from rich.console import Console
from rich.table import Table

from vera import ScoreRange
from vera.core import utils
from vera.core.configuration import CONFIG

if TYPE_CHECKING:
    from vera.core.data_models.csv import CsvRow
    from vera.core.utils import ScoreColor

type _TestCaseIdToScoreRange = dict[int, ScoreRange]
type _TestCaseIdToResults = dict[int, list[int | float]]
type _TestCaseIdToDurations = dict[int, list[dict[str, float]]]

ERR_MSG_MIN_MEN: int = 200


class ReportSummary:
    __slots__ = ("all_durations", "all_runs_rows", "failed_tests", "ranges", "results")

    def __init__(
        self,
        all_runs_rows: list[list[Any]],
        failed_tests: list[tuple[Any, Exception]] | None = None,
        all_durations: list[dict[int, dict[str, float]]] | None = None,
    ) -> None:
        self.all_runs_rows: list[list[CsvRow]] = all_runs_rows
        self.results: _TestCaseIdToResults = defaultdict(list)
        self.ranges: _TestCaseIdToScoreRange = {}
        self.failed_tests: list[tuple[Any, Exception]] = failed_tests or []
        self.all_durations: _TestCaseIdToDurations = defaultdict(list)
        if all_durations:
            for run_durations in all_durations:
                for test_id, duration_data in run_durations.items():
                    self.all_durations[test_id].append(duration_data)

    def display(self) -> None:
        if not self.all_runs_rows and not self.failed_tests:
            return

        console: Console = Console()
        if self.failed_tests:
            self._display_failures(console)

        self._set_run_results_and_ranges()
        table: Table = self._build_summary_table()
        # Ensure the table is visible
        console.print(table)
        if (score := self._get_overall_score()) is not None:
            console.print(score)

    def _set_run_results_and_ranges(self) -> None:
        for run_rows in self.all_runs_rows:
            for row in run_rows:
                test_id: int = row.identifier
                self.results[test_id].append(row.final_score)
                if test_id not in self.ranges:
                    self.ranges[test_id] = row.score_range

    def _build_summary_table(self) -> Table:
        table: Table = Table(title="Test Summary", header_style="bold magenta")
        table.add_column("Test ID", style="cyan")
        table.add_column("Avg Score", justify="right")

        if CONFIG.verbose:
            table.add_column("Setup", justify="right")
            table.add_column("Feature", justify="right")
            table.add_column("Static", justify="right")
            table.add_column("LLM", justify="right")

        table.add_column("Total Time", justify="right")

        if len(self.all_runs_rows) > 1:
            table.add_column("Min Score", justify="right")
            table.add_column("Max Score", justify="right")
            table.add_column("Runs", justify="right")

        for test_id in sorted(self.results):
            scores: list[float] = self.results[test_id]
            avg_score: float = sum(scores) / len(scores)
            score_range: ScoreRange | None = self.ranges.get(test_id)
            color: ScoreColor = "white"
            if score_range is not None:
                color = utils.get_score_color(avg_score, score_range)

            avg_score_str = f"[{color}]{avg_score:.2f}[/{color}]"

            row_data = self._get_row_data(avg_score_str, test_id)

            if len(self.all_runs_rows) > 1:
                row_data.extend([f"{min(scores):.2f}", f"{max(scores):.2f}", str(len(scores))])

            table.add_row(*row_data)

        return table

    def _get_row_data(self, avg_score_str: str, test_id: int) -> list[str | Any]:
        durations_list = self.all_durations.get(test_id, [])
        if durations_list:
            avg_total = sum(d.get("total", 0) for d in durations_list) / len(durations_list)
            total_time_str = f"{avg_total:.2f}s"
            if CONFIG.verbose:
                avg_setup = sum(d.get("setup", 0) for d in durations_list) / len(durations_list)
                avg_feature = sum(d.get("feature", 0) for d in durations_list) / len(durations_list)
                avg_static = sum(d.get("static_eval", 0) for d in durations_list) / len(
                    durations_list
                )
                avg_llm = sum(d.get("llm_eval", 0) for d in durations_list) / len(durations_list)
                time_cols = [
                    f"{avg_setup:.2f}s",
                    f"{avg_feature:.2f}s",
                    f"{avg_static:.2f}s",
                    f"{avg_llm:.2f}s",
                ]
            else:
                time_cols = []
        else:
            total_time_str = "N/A"
            time_cols = ["N/A"] * 4 if CONFIG.verbose else []

        return [str(test_id), avg_score_str, *time_cols, total_time_str]

    def _display_failures(self, console: Console) -> None:
        table: Table = Table(title="Failed Tests", header_style="bold red", style="red")
        table.add_column("Test ID", style="cyan")
        table.add_column("Error", style="white")

        for test_case, error in self.failed_tests:
            error_msg: str = str(error)
            if len(error_msg) > ERR_MSG_MIN_MEN:
                error_msg = f"{error_msg[: ERR_MSG_MIN_MEN - 3]}..."

            table.add_row(str(test_case.id), error_msg)

        console.print(table)
        console.print()

    def _get_overall_score(self) -> str | None:
        all_scores: list[int | float] = [s for scores in self.results.values() for s in scores]
        if not all_scores:
            return None

        total_avg: float = sum(all_scores) / len(all_scores)
        first_range: ScoreRange | None = next(iter(self.ranges.values()), None)
        color: ScoreColor = "green"
        if first_range:
            color = utils.get_score_color(total_avg, first_range)

        return f"\n[bold {color}]Overall Average Score: {total_avg:.2f}[/bold {color}]"
