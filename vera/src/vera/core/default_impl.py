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
import io
import logging
from collections.abc import Iterable  # noqa: TC003
from string import Template

import anyio
from rich.progress import Progress, TaskID  # noqa: TC002

from vera.core.data_models.llm_sdk import LlmConfig
from vera.hook_impl import hook_impl
from vera.project_name import PROJECT_NAME

from . import constants
from .configuration import CONFIG
from .data_models.csv import CsvColumn, CsvRow
from .data_models.test_case import TestCase  # noqa: TC001
from .data_models.test_case.input import TestCaseInput
from .data_models.test_case.output import TestCaseOutput
from .gemini import Gemini, GeminiConfig
from .hook_specs import PluginService  # noqa: TC001
from .rich_cli_service import RichCliService
from .write_results_to_file import write_to_file

logger: logging.Logger = logging.getLogger(PROJECT_NAME)


@hook_impl
def get_cli_service(progress: Progress, task_id: TaskID) -> RichCliService:
    return RichCliService(progress, task_id)


@hook_impl
async def llm_evaluation[T_Input: TestCaseInput, T_Output: TestCaseOutput, T_LlmConfig: LlmConfig](
    test_case: TestCase[T_Input],
    test_output: T_Output,
    plugin_service: PluginService,
) -> CsvColumn:
    specs_path: anyio.Path = plugin_service.get_llm_specs_dir()
    specs: tuple[str, ...] = await plugin_service.get_spec_files(specs_dir=specs_path)
    llm_config: T_LlmConfig = plugin_service.get_llm_configuration()
    async with plugin_service.get_llm_sdk(config=llm_config) as llm:
        system_prompt: io.StringIO = io.StringIO()
        for s in specs:
            system_prompt.write(s)
            system_prompt.write("\n\n")

        llm.set_system_prompt_to_session(system_prompt.getvalue())

        resources_dir: anyio.Path = plugin_service.get_resources_dir()
        prompt: str = await plugin_service.create_evaluation_task_prompt(
            resources_dir=resources_dir,
            test_case=test_case,
            test_output=test_output,
        )
        schema: type[CsvColumn] = plugin_service.get_llm_csv_columns_class()
        return await llm.send_message(
            prompt,
            response_json_schema=schema,
            raise_error_if_empty_response=True,
        )


@hook_impl
def get_llm_configuration() -> GeminiConfig:
    return GeminiConfig()


@hook_impl
def get_llm_sdk(config: GeminiConfig) -> Gemini:
    return Gemini(config)


@hook_impl
async def publish_results[
    T_In: TestCaseInput,
    T_Out: TestCaseOutput,
    T_Col1: CsvColumn,
    T_Col2: CsvColumn,
](rows: Iterable[CsvRow[T_In, T_Out, T_Col1, T_Col2]], _: int = 0) -> None:
    if not CONFIG.enable_csv_report:
        logger.debug("CSV report generation is disabled")
        return

    await write_to_file(rows)


@hook_impl
async def create_evaluation_task_prompt[
    T_Input: TestCaseInput,
    T_Output: TestCaseOutput,
](
    resources_dir: anyio.Path,
    test_case: TestCase[T_Input],
    test_output: T_Output,
) -> str:
    prompt_file: anyio.Path = anyio.Path(__file__).parent / "prompts" / "test_task.md"
    task_prompt: str = await prompt_file.read_text(encoding="utf-8")

    example_output: str = "N/A"
    if test_case.expected_output is not None:
        example_output = str(await test_case.expected_output.get_expected_output(resources_dir))

    return Template(task_prompt).substitute(
        formatted_input_string=test_case.input.to_description_prompt(),
        actual_output_string=test_output.to_output_description_prompt(),
        example_output=example_output,
    )


@hook_impl
async def get_spec_files(specs_dir: anyio.Path) -> tuple[str, ...]:
    return await asyncio.gather(
        get_scoring_rubric_spec(specs_dir),
        get_additional_context_spec(specs_dir),
        get_concept_definition_spec(specs_dir),
        get_golden_dataset_spec(specs_dir),
        get_safety_constraints_spec(specs_dir),
        get_style_guidelines_spec(specs_dir),
    )


@hook_impl
async def get_additional_context_spec(specs_dir: anyio.Path) -> str:
    file: anyio.Path = specs_dir / constants.ADDITIONAL_CONTEXT_FILE
    return await file.read_text(encoding="utf-8")


@hook_impl
async def get_concept_definition_spec(specs_dir: anyio.Path) -> str:
    file: anyio.Path = specs_dir / constants.CONCEPT_DEFINITION_FILE
    return await file.read_text(encoding="utf-8")


@hook_impl
async def get_golden_dataset_spec(specs_dir: anyio.Path) -> str:
    file: anyio.Path = specs_dir / constants.GOLDEN_DATASET_FILE
    return await file.read_text(encoding="utf-8")


@hook_impl
async def get_safety_constraints_spec(specs_dir: anyio.Path) -> str:
    file: anyio.Path = specs_dir / constants.SAFETY_CONSTRAINTS_FILE
    return await file.read_text(encoding="utf-8")


@hook_impl
async def get_scoring_rubric_spec(specs_dir: anyio.Path) -> str:
    file: anyio.Path = specs_dir / constants.SCORING_RUBRIC_FILE
    return await file.read_text(encoding="utf-8")


@hook_impl
async def get_style_guidelines_spec(specs_dir: anyio.Path) -> str:
    file: anyio.Path = specs_dir / constants.STYLE_GUIDELINES_FILE
    return await file.read_text(encoding="utf-8")
