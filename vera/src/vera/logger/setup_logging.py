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

import atexit
import json
import logging.config
import logging.handlers
import os
from pathlib import Path
from typing import Any, cast

__all__: list[str] = ["setup_logging"]

LOG_CONFIG_FILE_NAME: str = "logger_config.json"


def setup_logging(level: str = "INFO", *, verbose: bool = False) -> None:
    """Setup logging configuration"""
    config_file: Path = Path(__file__).parent / LOG_CONFIG_FILE_NAME
    config: dict[str, Any] = json.loads(config_file.read_text(encoding="UTF-8"))
    config["loggers"]["root"]["level"] = level
    config["handlers"]["console"]["show_path"] = verbose

    if _is_running_in_pytest():
        config["loggers"]["root"]["handlers"] = ["console"]
        logging.config.dictConfig(config)
        return

    logging.config.dictConfig(config)
    _set_other_noisy_loggers_level(verbose=verbose)

    queue_handler: logging.handlers.QueueHandler | None = cast(
        "logging.handlers.QueueHandler", logging.getHandlerByName("queue_handler")
    )
    if queue_handler is not None and queue_handler.listener is not None:
        try:
            queue_handler.listener.start()
            atexit.register(queue_handler.listener.stop)
        except RuntimeError:
            # Already started
            pass


def _is_running_in_pytest() -> bool:
    return "PYTEST_CURRENT_TEST" in os.environ


def _set_other_noisy_loggers_level(*, verbose: bool) -> None:
    extra_level: int = logging.NOTSET if verbose else logging.WARNING
    for logger_name in ("google", "google_genai", "urllib3", "httpx"):
        logging.getLogger(logger_name).setLevel(extra_level)
