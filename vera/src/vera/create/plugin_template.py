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

import string
from typing import TYPE_CHECKING, NamedTuple, TypedDict

if TYPE_CHECKING:
    from pathlib import Path

PROJECT_FILE: str = "pyproject.toml"
TEMPLATE_PLUGIN_NAME: str = "plugin_name"


class PluginDetails(NamedTuple):
    name: str
    description: str


class ProjectFileSubstitution(TypedDict):
    description: str
    project_name: str
    plugin_name: str


def populate(template: Path, details: PluginDetails) -> None:
    _change_template_names_glob(template, TEMPLATE_PLUGIN_NAME, details.name)
    _replace_template_placeholders(template, details)


def _change_template_names_glob(path: Path, /, name_to_change: str, new_name: str) -> None:
    for p in path.rglob(f"{name_to_change}*"):
        p.rename(p.parent / new_name)

    for p in path.rglob(f"test_{name_to_change}*"):
        p.rename(p.parent / f"test_{new_name}")


def _replace_template_placeholders(base_path: Path, details: PluginDetails) -> None:
    substitution: ProjectFileSubstitution = _get_project_file_substitution(details)
    for file in base_path.rglob("*"):
        if file.is_dir() or file.suffix == ".pyc" or "__pycache__" in str(file):
            continue

        try:
            content: str = file.read_text(encoding="utf-8")
            if file.name == PROJECT_FILE:
                template: string.Template = string.Template(content)
                file.write_text(template.safe_substitute(substitution), encoding="utf-8")

            elif f"${{{TEMPLATE_PLUGIN_NAME}}}" in content:
                template: string.Template = string.Template(content)
                sub: dict[str, str] = {TEMPLATE_PLUGIN_NAME: details.name}
                file.write_text(template.safe_substitute(**sub), encoding="utf-8")
        except OSError, UnicodeDecodeError:
            continue


def _create_project_name(plugin_name: str) -> str:
    return plugin_name.replace("_", "-")


def _get_project_file_substitution(details: PluginDetails) -> ProjectFileSubstitution:
    return ProjectFileSubstitution(
        description=details.description or "Add your description here",
        project_name=_create_project_name(details.name),
        plugin_name=details.name,
    )
