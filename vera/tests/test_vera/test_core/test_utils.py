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
import dataclasses
from typing import TYPE_CHECKING

from vera.core.utils import (
    create_plugin_name_display_repr,
    filter_taggables_by_tags,
    syncify,
)
from vera.project_name import PROJECT_NAME

if TYPE_CHECKING:
    from collections.abc import Iterable


def test_create_plugin_name_display_repr() -> None:
    names = ["plugin1", f"{PROJECT_NAME}.core.default_impl", "plugin2"]
    result = create_plugin_name_display_repr(names)
    assert "plugin1" in result
    assert "plugin2" in result
    assert f"{PROJECT_NAME}.core.default_impl" not in result
    assert result == "    [green]- plugin1[/green]\n    [green]- plugin2[/green]"


@dataclasses.dataclass
class MockTaggable:
    tags: Iterable[str]


def test_filter_taggables_by_tags() -> None:
    t1 = MockTaggable(["tag1", "tag2"])
    t2 = MockTaggable(["tag2", "tag3"])
    t3 = MockTaggable(["tag4"])
    taggables = [t1, t2, t3]

    # No tags filter
    assert filter_taggables_by_tags(taggables, []) == taggables

    # Filter by one tag
    assert filter_taggables_by_tags(taggables, ["tag1"]) == [t1]
    assert filter_taggables_by_tags(taggables, ["tag2"]) == [t1, t2]

    # Filter by multiple tags
    assert filter_taggables_by_tags(taggables, ["tag1", "tag4"]) == [t1, t3]

    # No match
    assert filter_taggables_by_tags(taggables, ["nonexistent"]) == []


def test_syncify() -> None:
    @syncify
    async def async_func(x: int, y: int) -> int:
        await asyncio.sleep(0.01)
        return x + y

    result: int = async_func(1, 2)
    assert result == 3
