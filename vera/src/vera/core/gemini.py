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

import io
import logging
from typing import TYPE_CHECKING, Any, Self, override

from google import genai
from google.genai.errors import ClientError
from google.genai.types import (
    Content,
    GenerateContentConfig,
    GoogleSearch,
    HarmBlockThreshold,
    HarmCategory,
    Part,
    SafetySetting,
    ThinkingConfig,
    ThinkingLevel,
    Tool,
    ToolListUnion,
    UrlContext,
)
from pydantic import BaseModel
from tenacity import (
    after_log,
    before_log,
    retry,
    retry_if_not_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from vera.core import exceptions
from vera.core.configuration import VeraConfig
from vera.project_name import PROJECT_NAME

from .data_models.llm_config import LlmConfig
from .data_models.llm_sdk import LlmSdk

if TYPE_CHECKING:
    from types import TracebackType


logger: logging.Logger = logging.getLogger(PROJECT_NAME)


class GeminiConfig(LlmConfig):
    model_name: str = "gemini-3-pro-preview"
    temperature: float = 1.0
    sexually_explicit: str = "OFF"
    dangerous_content: str = "OFF"
    hate_speach: str = "OFF"
    harassment: str = "OFF"
    google_search: bool = True
    url_context: bool = True
    use_thinking: bool = True

    @property
    def api_key(self) -> str:
        config: VeraConfig = VeraConfig.load()
        if config.gemini_api_key:
            return config.gemini_api_key

        msg: str = (
            "Could not find a saved Gemini API key in the configuration. "
            "Please configure it using 'vera config -k'."
        )
        raise exceptions.ApiKeyNotFoundError(msg) from None


class Gemini(LlmSdk[GeminiConfig]):
    def __init__(self, config: GeminiConfig) -> None:
        super().__init__(config)
        self.client: genai.client.AsyncClient = genai.client.Client(api_key=self.config.api_key).aio
        self.model: str = self.config.model_name
        self.contents: list[Content] = []

    @override
    async def __aenter__(self) -> Self:
        return self

    @override
    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        await self.close()

    @override
    @retry(
        retry=retry_if_not_exception_type(ClientError),
        stop=stop_after_attempt(4),
        wait=wait_exponential(),
        after=after_log(logger, logging.DEBUG),
        before=before_log(logger, logging.DEBUG),
    )
    async def send_message[T: BaseModel](
        self,
        prompt: str,
        /,
        *,
        raise_error_if_empty_response: bool = False,
        response_json_schema: type[T] | None = None,
    ) -> T | str:
        logger.debug("Sending prompt: %s", prompt)
        self.contents.append(Content(role="user", parts=[Part.from_text(text=prompt)]))

        response: str = await self._generate_response(response_json_schema)
        logger.debug("Response text: %s", response)
        if raise_error_if_empty_response and not response:
            msg: str = f"Received {response!r} from the LLM as generation results"
            logger.error(msg)
            raise ValueError(msg)

        if response:
            content: Content = Content(role="model", parts=[Part.from_text(text=response)])
            self.contents.append(content)

        if response_json_schema is not None and response:
            try:
                return response_json_schema.model_validate_json(response, by_alias=True)
            except Exception:
                logger.exception(
                    "Failed to validate response against schema. Response text: %s", response
                )
                raise

        return response

    async def _generate_response(self, response_json_schema: type[BaseModel] | None) -> str:
        schema: dict[str, Any] | None = None
        if response_json_schema is not None:
            schema = response_json_schema.model_json_schema()

        config: GenerateContentConfig = self.create_generate_content_config(schema)
        response: io.StringIO = io.StringIO()
        try:
            async for chunk in await self.client.models.generate_content_stream(
                model=self.model,
                contents=self.contents,
                config=config,
            ):
                if chunk.text:
                    response.write(chunk.text)

        except ClientError:
            logger.exception("Failed to generate content")
            raise

        return response.getvalue()

    async def close(self) -> None:
        self.clean_session_history()
        await self.client.aclose()

    @override
    def clean_session_history(self) -> None:
        self.contents.clear()

    @override
    def add_system_prompts_to_session(self, *prompts: str) -> None:
        if self.contents:
            return

        for prompt in prompts:
            self.contents.append(Content(role="user", parts=[Part.from_text(text=prompt)]))

    def create_generate_content_config(
        self,
        response_json_schema: dict[str, Any] | None = None,
    ) -> GenerateContentConfig:
        response_mime_type: str = "plain/text"
        if response_json_schema is not None:
            response_mime_type = "application/json"

        tools: ToolListUnion = self._get_tools()
        safety_settings: list[SafetySetting] = self._get_safety_settings()
        thinking_config: ThinkingConfig | None = self._get_thinking_config()
        return GenerateContentConfig(
            temperature=self.config.temperature,
            response_mime_type=response_mime_type,
            thinking_config=thinking_config,
            response_json_schema=response_json_schema,
            tools=tools,
            safety_settings=safety_settings,
        )

    def _get_safety_settings(self) -> list[SafetySetting]:
        try:
            return [
                SafetySetting(
                    category=HarmCategory.HARM_CATEGORY_HARASSMENT,
                    threshold=HarmBlockThreshold(self.config.harassment),
                ),
                SafetySetting(
                    category=HarmCategory.HARM_CATEGORY_HATE_SPEECH,
                    threshold=HarmBlockThreshold(self.config.hate_speach),
                ),
                SafetySetting(
                    category=HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
                    threshold=HarmBlockThreshold(self.config.dangerous_content),
                ),
                SafetySetting(
                    category=HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
                    threshold=HarmBlockThreshold(self.config.sexually_explicit),
                ),
            ]
        except ValueError as e:
            msg: str = "Invalid HarmBlockThreshold value. Value must be an integer between 0 and 5"
            raise ValueError(msg) from e

    def _get_tools(self) -> ToolListUnion:
        results: ToolListUnion = []
        if self.config.google_search:
            results.append(Tool(google_search=GoogleSearch()))

        if self.config.url_context:
            results.append(Tool(url_context=UrlContext()))

        return results

    def _get_thinking_config(self) -> ThinkingConfig | None:
        return (
            ThinkingConfig(thinking_level=ThinkingLevel.HIGH) if self.config.use_thinking else None
        )
