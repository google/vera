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

import abc
from contextlib import AbstractAsyncContextManager
from typing import TYPE_CHECKING, Literal, Self, overload, override

from pydantic import BaseModel

from .llm_config import LlmConfig

if TYPE_CHECKING:
    from types import TracebackType


class LlmSdk(AbstractAsyncContextManager, abc.ABC):
    @abc.abstractmethod
    def __init__[T: LlmConfig](self, llm_config: T) -> None:
        self.llm_config: T = llm_config

    @overload
    async def send_message[T_Schema: BaseModel](
        self,
        prompt: str,
        /,
        *,
        raise_error_if_empty_response: Literal[True],
        response_json_schema: type[T_Schema],
    ) -> T_Schema: ...

    @overload
    async def send_message[T_Schema: BaseModel](
        self,
        prompt: str,
        /,
        *,
        raise_error_if_empty_response: Literal[False],
        response_json_schema: type[T_Schema],
    ) -> T_Schema | Literal[""]: ...

    @overload
    async def send_message(
        self,
        prompt: str,
        /,
        *,
        raise_error_if_empty_response: bool,
        response_json_schema: None = None,
    ) -> str: ...

    @abc.abstractmethod
    async def send_message[T_Schema: BaseModel](
        self,
        prompt: str,
        /,
        *,
        raise_error_if_empty_response: bool,
        response_json_schema: type[T_Schema] | None = None,
    ) -> T_Schema | str: ...

    @abc.abstractmethod
    def clean_session_history(self) -> None: ...

    @abc.abstractmethod
    def add_system_prompts_to_session(self, *prompts: str) -> None: ...

    @override
    @abc.abstractmethod
    async def __aenter__(self) -> Self: ...

    @override
    @abc.abstractmethod
    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None: ...
