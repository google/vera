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

from pathlib import Path
from typing import Any, Self, cast

import yaml
from platformdirs import user_config_dir
from pydantic import BaseModel, ConfigDict
from pydantic_core import PydanticUndefined

from vera.project_name import PROJECT_NAME

CONFIG_FILE_NAME = "config.yaml"


class VeraConfig[T](BaseModel):
    model_config = ConfigDict(extra="allow")

    dst_dir: Path | None = None
    gemini_api_key: str | None = None
    report_name: str = "report"
    enable_csv_report: bool = True
    log_level: str = "INFO"
    verbose: bool = False

    @classmethod
    def get(cls) -> Self:
        """Returns the global configuration instance cast to the current class type.

        This allows for IDE support when extending VeraConfig.

        Returns:
            Self: The global configuration instance.

        """
        return CONFIG.as_type(cls)

    def as_type[U](self, _cls: type[U], /) -> U:
        """Casts the config instance to a specific type or Protocol.

        Example:
            >>> class MyProtocol(Protocol):
            ...     my_attr: str
            >>> config.as_type(MyProtocol).my_attr

        Returns:
            U: The cast config instance.

        Raises:
            ValueError: If a field has no default value and no factory.
            TypeError: If the provided class is not a type.

        """
        if not isinstance(_cls, type) or not issubclass(_cls, BaseModel):
            msg: str = f"Expected type, got {_cls.__class__.__name__}"
            raise TypeError(msg)

        for name, field_info in _cls.model_fields.items():
            if not hasattr(self, name):
                if field_info.default is not PydanticUndefined:
                    setattr(self, name, field_info.default)
                elif field_info.default_factory is not None:
                    setattr(self, name, field_info.default_factory())
                else:
                    msg: str = f"Field '{name}' has no default value and no factory"
                    raise ValueError(msg)

        return cast("U", self)

    @property
    def ext(self) -> T:
        """Returns the config instance cast to the generic extension type T.

        Example:
            >>> config: VeraConfig[MyProtocol] = VeraConfig.get()
            >>> config.ext.my_attr

        Returns:
            T: The cast config instance.

        """
        return cast("T", self)

    @classmethod
    def load(cls) -> Self:
        config_path: Path = get_config_path()
        if not config_path.exists():
            return cls()

        try:
            with config_path.open(encoding="utf-8") as f:
                data: dict[str, Any] = yaml.safe_load(f)

            if data.get("dst_dir"):
                data["dst_dir"] = Path(data["dst_dir"])

            return cls.model_validate(data)

        except yaml.YAMLError, OSError:
            return cls()

    def save(self) -> None:
        config_path: Path = get_config_path()
        config_path.parent.mkdir(parents=True, exist_ok=True)

        data: dict[str, Any] = self.model_dump()
        if data["dst_dir"]:
            data["dst_dir"] = str(data["dst_dir"])

        with config_path.open("w", encoding="utf-8") as f:
            yaml.safe_dump(data, f, indent=4)


def get_config_path() -> Path:
    return Path(user_config_dir(appname=PROJECT_NAME)) / CONFIG_FILE_NAME


CONFIG: VeraConfig = VeraConfig.load()
