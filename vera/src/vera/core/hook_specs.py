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

from collections.abc import Iterable  # noqa: TC003
from contextlib import AbstractAsyncContextManager  # noqa: TC003
from typing import Protocol

import anyio  # noqa: TC002
import pluggy
from pluggy import HookspecMarker
from typer import Typer  # noqa: TC002

from vera.core.configuration import VeraConfig  # noqa: TC001
from vera.core.data_models.llm_config import LlmConfig
from vera.project_name import PROJECT_NAME

from .data_models.cli_service import CliService  # noqa: TC001
from .data_models.csv import CsvColumn, CsvRow
from .data_models.llm_sdk import LlmSdk  # noqa: TC001
from .data_models.test_case import TestCase  # noqa: TC001
from .data_models.test_case.input import TestCaseInput
from .data_models.test_case.output import TestCaseOutput

hook_spec: HookspecMarker = pluggy.HookspecMarker(PROJECT_NAME)


class PluginService[T_Input: TestCaseInput, T_Output: TestCaseOutput, T_Row: CsvRow](Protocol):  # noqa: PLR0904
    """Defines the hook specifications for Eve plugins.

    Plugins should implement these hooks to provide feature-specific evaluation logic.
    """

    @staticmethod
    @hook_spec(firstresult=True)
    def get_test_cases() -> Iterable[TestCase[T_Input]]:
        """Returns an iterable of test cases to be evaluated.

        Typically, loads data from a YAML or JSON file.
        """

    @staticmethod
    @hook_spec(firstresult=True)
    def get_cli_service[P, T](progress: P, task_id: T) -> CliService[P, T]:
        """Returns a CLI service implementation for reporting progress.

        The default implementation uses Rich.
        """

    @staticmethod
    @hook_spec(firstresult=True)
    async def run_feature(test_case: TestCase[T_Input], resources_dir: anyio.Path) -> T_Output:
        """Executes the feature being tested using the provided test case.

        Should return the feature's output encapsulated in a TestCaseOutput model.
        """

    @staticmethod
    @hook_spec(firstresult=True)
    def run_static_tests(test_case: TestCase[T_Input], test_output: T_Output) -> CsvColumn:
        """Performs programmatic (static) evaluation of the feature output.

        Returns a CsvColumn containing the results of these checks.
        """

    @staticmethod
    @hook_spec(firstresult=True)
    def get_csv_row_class() -> type[T_Row]:
        """Returns the Pydantic class used to represent a row in the final CSV report."""

    @staticmethod
    @hook_spec(firstresult=True)
    def get_llm_csv_columns_class() -> type[CsvColumn]:
        """Returns the Pydantic class used to represent the LLM Judge's evaluation columns."""

    @staticmethod
    @hook_spec(firstresult=True)
    async def llm_evaluation(
        test_case: TestCase[T_Input],
        test_output: T_Output,
        plugin_service: PluginService,
    ) -> CsvColumn:
        """Performs the LLM-as-a-Judge evaluation.

        The default implementation sends a prompt to Gemini using the provided specs.
        """

    @staticmethod
    @hook_spec(firstresult=True)
    def get_llm_configuration[T: LlmConfig]() -> T:
        """Returns the LLM configuration (model name, temperature, etc.) for the LLM Judge."""

    @staticmethod
    @hook_spec(firstresult=True)
    def get_llm_sdk[T: LlmConfig](config: T) -> AbstractAsyncContextManager[LlmSdk[T]]:
        """Returns the LLM context manager object."""

    @staticmethod
    @hook_spec(firstresult=True)
    def get_llm_specs_dir() -> anyio.Path:
        """Returns the path to the directory containing Markdown evaluation specs."""

    @staticmethod
    @hook_spec(firstresult=True)
    def get_resources_dir() -> anyio.Path:
        """Returns the path to the directory containing resources (context files, images, etc.)"""

    @staticmethod
    @hook_spec
    async def publish_results(rows: Iterable[T_Row], run_index: int) -> None:
        """Called after all evaluations are complete for a single suite run.

        Used to save results to a file, database, or external service.
        """

    @staticmethod
    @hook_spec
    def display_test_command_help(extra_args: list[str]) -> bool | None:
        """Displays help for additional CLI arguments for the 'eval' command.

        Plugins should check if their specific help flag is present in extra_args,
        print the help message, remove the flag, and return True.
        """

    @staticmethod
    @hook_spec
    def handle_test_command_extra_args(extra_args: list[str]) -> None:
        """Handles additional CLI arguments passed to the 'eval' command.

        Plugins should remove recognized arguments from the list.
        """

    @staticmethod
    @hook_spec
    def display_config_command_help(extra_args: list[str]) -> bool | None:
        """Displays help for additional CLI arguments for the 'config' command.

        Plugins should check if their specific help flag is present in extra_args,
        print the help message, remove the flag, and return True.
        """

    @staticmethod
    @hook_spec
    def handle_config_command_extra_args(config: VeraConfig, extra_args: list[str]) -> None:
        """Handles additional CLI arguments passed to the 'config' command.

        Plugins should remove recognized arguments from the list.
        """

    @staticmethod
    @hook_spec
    def update_configuration(config: VeraConfig) -> None:
        """Allows plugins to modify the global configuration object after it's loaded."""

    @staticmethod
    @hook_spec
    def handle_config_command_display(config: VeraConfig) -> None:
        """Allows plugins to display their specific configuration when 'vera config' is run without
        arguments.
        """

    @staticmethod
    @hook_spec
    def extend_cli(app: Typer) -> None:
        """Allows plugins to add new commands or subcommands to the Eve CLI."""

    @staticmethod
    @hook_spec(firstresult=True)
    async def create_evaluation_task_prompt(
        resources_dir: anyio.Path,
        test_case: TestCase[T_Input],
        test_output: T_Output,
    ) -> str:
        """Constructs the prompt that will be sent to the LLM Judge."""

    @staticmethod
    @hook_spec(firstresult=True)
    async def get_spec_files(specs_dir: anyio.Path) -> tuple[str, ...]:
        """Gathers all the spec file contents to be sent as system instructions to the LLM."""

    @staticmethod
    @hook_spec(firstresult=True)
    async def get_additional_context_spec(specs_dir: anyio.Path) -> str:
        """Returns the content of the additional_context.md spec."""

    @staticmethod
    @hook_spec(firstresult=True)
    async def get_concept_definition_spec(specs_dir: anyio.Path) -> str:
        """Returns the content of the concept_definition.md spec."""

    @staticmethod
    @hook_spec(firstresult=True)
    async def get_golden_dataset_spec(specs_dir: anyio.Path) -> str:
        """Returns the content of the golden_dataset.md spec."""
        ...

    @staticmethod
    @hook_spec(firstresult=True)
    async def get_safety_constraints_spec(specs_dir: anyio.Path) -> str:
        """Returns the content of the safety_constraints.md spec."""

    @staticmethod
    @hook_spec(firstresult=True)
    async def get_scoring_rubric_spec(specs_dir: anyio.Path) -> str:
        """Returns the content of the scoring_rubric.md spec."""

    @staticmethod
    @hook_spec(firstresult=True)
    async def get_style_guidelines_spec(specs_dir: anyio.Path) -> str:
        """Returns the content of the style_guidelines.md spec."""
