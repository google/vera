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
import functools
from typing import TYPE_CHECKING, Any, Literal, Protocol

from vera.project_name import PROJECT_NAME

if TYPE_CHECKING:
    from collections.abc import Callable, Coroutine, Iterable

    from .data_models.csv import ScoreRange

NORMALIZED_TEST_SCORE_UPPER_BOUND: float = 0.8
NORMALIZED_TEST_SCORE_LOWER_BOUND: float = 0.4

type ScoreColor = Literal["white", "green", "yellow", "red"]


def create_plugin_name_display_repr(names: Iterable[str]) -> str:
    return "\n".join(
        f"    [green]- {name}[/green]"
        for name in names
        if f"{PROJECT_NAME}.core.default_impl" not in name
    )


class Taggable(Protocol):
    tags: Iterable[str]


def filter_taggables_by_tags[T: Taggable](taggables: Iterable[T], tags: Iterable[str]) -> list[T]:
    tags_list: list[str] = list(tags)
    if not tags_list:
        return list(taggables)

    return [t for t in taggables if set(t.tags).intersection(tags_list)]


def syncify[**P, R](
    f: Callable[P, Coroutine[Any, Any, R]],
) -> Callable[P, R]:
    @functools.wraps(f)
    def _run_async(*args: Any, **kwargs: Any) -> R:  # noqa: ANN401
        return asyncio.run(f(*args, **kwargs))

    return _run_async


def get_score_color(score: float, score_range: ScoreRange) -> ScoreColor:
    if score_range.max <= score_range.min:
        return "white"

    normalized: int | float = (score - score_range.min) / (score_range.max - score_range.min)
    if normalized >= NORMALIZED_TEST_SCORE_UPPER_BOUND:
        return "green"

    if normalized >= NORMALIZED_TEST_SCORE_LOWER_BOUND:
        return "yellow"

    return "red"
