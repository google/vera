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
import logging
from pathlib import Path  # noqa: TC003
from typing import TYPE_CHECKING, Annotated, Any, override

import typer
from rich.console import Console, ConsoleRenderable
from rich.progress import (
    BarColumn,
    Progress,
    ProgressColumn,
    SpinnerColumn,
    Task,
    TaskID,
    TextColumn,
    TimeElapsedColumn,
)
from rich.text import Text

from vera.core import plugin_service, utils
from vera.core.configuration import CONFIG
from vera.logger import setup_logging
from vera.project_name import PROJECT_NAME

from .vtest import TestingService
from .vtest_setup import TestSetup
from .vtest_summary import ReportSummary

if TYPE_CHECKING:
    from collections.abc import Iterable

    from vera.core.data_models.test_case import TestCase
    from vera.core.hook_specs import CliService
    from vera.core.plugin_service import PluginCreation

app: typer.Typer = typer.Typer(help="Test features.")
logger: logging.Logger = logging.getLogger(PROJECT_NAME)


class SmartProgressColumn(ProgressColumn):
    @override
    def render(self, task: Task) -> ConsoleRenderable:
        if task.description == "[bold green]Total Progress[/bold green]":
            return Text(f"{int(task.completed)}/{int(task.total or 0)}")
        return Text(f"{task.percentage:>3.0f}%")


@app.command(
    name="test",
    help="Test installed features.",
    context_settings={"allow_extra_args": True, "ignore_unknown_options": True},
)
@utils.syncify
async def vtest_feature(  # noqa: PLR0913
    context: typer.Context,
    test_tags: Annotated[
        list[str],
        typer.Option(
            "--test-tag",
            "-t",
            help="Only tests that contain the specified tags will run",
            default_factory=list,
        ),
    ],
    dst_dir: Annotated[
        Path | None,
        typer.Option(
            "--dst-dir",
            "-d",
            help="The destination directory where the results csv files will be written into",
        ),
    ] = None,
    runs_count: Annotated[
        int,
        typer.Option("--runs-count", "-r", help="The number of times the test suite will run"),
    ] = 1,
    *,
    verbose: Annotated[bool, typer.Option("--verbose", "-v", help="Use verbose output")] = False,
    quiet: Annotated[bool, typer.Option("--quiet", "-q", help="Do not print any output")] = False,
    create_csv: Annotated[bool, typer.Option(help="Enable/Disable CSV report generation")] = True,
) -> None:
    _handle_logging(quiet=quiet, verbose=verbose)
    logger.debug(
        "Running test command with options: test_tags=%s, dst_dir=%s, runs_count=%s",
        test_tags,
        dst_dir,
        runs_count,
    )
    pc: PluginCreation = plugin_service.create_service()
    setup: TestSetup = TestSetup(pc)
    setup.handle_command_extrac_args(context).log_plugin_names().validate_llm_api_key()

    if runs_count < 1:
        logger.error("Run count must be greater than 0")
        raise typer.Exit(1)

    if dst_dir:
        CONFIG.dst_dir = dst_dir
    if not create_csv:
        CONFIG.enable_csv_report = False

    CONFIG.verbose = verbose

    test_cases: list[TestCase[Any]] = list(_get_filtered_test_cases(test_tags, pc))
    progress: Progress = Progress(
        SpinnerColumn(),
        TextColumn(text_format="[progress.description]{task.description}"),
        BarColumn(),
        SmartProgressColumn(),
        TimeElapsedColumn(),
        disable=quiet,
        transient=True,
    )
    testing_services: list[TestingService] = []
    try:
        with progress:
            task_id: TaskID = progress.add_task(
                description="[bold green]Total Progress[/bold green]",
                total=runs_count * len(test_cases),
            )
            cli_service: CliService[Progress, TaskID] = pc.plugin_service.get_cli_service(
                progress=progress,
                task_id=task_id,
            )
            async with asyncio.TaskGroup() as tg:
                for _ in range(runs_count):
                    es = TestingService(test_cases, pc.plugin_service, cli_service)
                    testing_services.append(es)
                    tg.create_task(es.run_tests())
    finally:
        console = Console()
        if not quiet and testing_services:
            console.print()
            console.rule("[bold]Results[/bold]")

        await asyncio.gather(
            *(es.publish_results(run_index=i) for i, es in enumerate(testing_services))
        )

        if not quiet and testing_services:
            console.rule("[bold]Summary[/bold]")
            all_runs_rows: list[list[Any]] = [es.csv_rows for es in testing_services]
            all_failed_tests: list[tuple[Any, Exception]] = []
            all_durations: list[dict[int, dict[str, float]]] = []
            for es in testing_services:
                all_failed_tests.extend(es.failed_test_cases)
                all_durations.append(es.durations)
            ReportSummary(all_runs_rows, all_failed_tests, all_durations).display()


def _handle_logging(*, quiet: bool, verbose: bool) -> None:
    if verbose:
        setup_logging(level="DEBUG", verbose=True)
    elif quiet:
        setup_logging(level="ERROR")


def _get_filtered_test_cases(test_tags: list[str], pc: PluginCreation) -> Iterable[TestCase[Any]]:
    logger.debug("Fetching test cases from plugin service")
    test_cases: Iterable[TestCase[Any]] = pc.plugin_service.get_test_cases()
    logger.debug("Filtering test cases with tags: %s", test_tags)
    test_cases = utils.filter_taggables_by_tags(test_cases, test_tags)
    logger.debug(
        "Found %s test cases after filtering",
        len(list(test_cases)) if hasattr(test_cases, "__len__") else "some",
    )
    if not test_cases:
        logger.error("[red]Found no tests to run.[/red]")
        if test_tags:
            logger.error("[red]Check if the specified tags exist in any of the test cases[/red]")

        raise typer.Exit(1)

    return test_cases
