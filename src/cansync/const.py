import os
import re
import logging
from pathlib import Path
from enum import StrEnum

from typing import Final, Any, Callable
from cansync.types import ConfigDict, TuiStyle
from cansync.utils import verify_accessible_path


logger = logging.getLogger(__name__)


URL_REGEX: Final[str] = (
    r"[(http(s)?):\/\/(www\.)?a-zA-Z0-9@:%._\+~#=]{2,256}\.[a-z]{2,6}\b([-a-zA-Z0-9@:%_\+.~#?&\/\/=]*)"
)
API_KEY_REGEX: Final[str] = r"\d{4}~[A-Za-z0-9]{64}"

HOME: Final[Path] = Path(
    os.getenv(
        "HOME", os.getenv("HOMEDRIVE", os.getenv("HOMESHARE", "this is an issue"))
    )
)
XDG_CACHE_DIR: Final[Path] = Path(os.getenv("XDG_CACHE_HOME", HOME / ".cache"))
XDG_CONFIG_DIR: Final[Path] = Path(os.getenv("XDG_CONFIG_HOME", HOME / ".config"))

CACHE_DIR: Final[Path] = XDG_CACHE_DIR / "cansync"
LOG_FN: Final[Path] = CACHE_DIR / "cansync.log"

CONFIG_DIR: Final[Path] = XDG_CONFIG_DIR / "cansync"
CONFIG_FN: Final[Path] = CONFIG_DIR / "config.toml"

DEFAULT_DOWNLOAD_DIR: Final[Path] = HOME / "Documents" / "Cansync"

CONFIG_DEFAULTS: Final[ConfigDict] = {
    "url": "",
    "api_key": "",
    "storage_path": str(DEFAULT_DOWNLOAD_DIR),
    "course_ids": [],
}
CONFIG_KEY_DEFINITIONS: Final[dict[str, str]] = {
    "url": "Canvas URL",
    "api_key": "API key",
    "storage_path": "Storage path",
    "course_ids": "Course ID number(s)",
}
CONFIG_VALIDATORS: Final[dict[str, Callable]] = {
    "url": lambda s: re.match(URL_REGEX, s),
    "api_key": lambda s: re.match(API_KEY_REGEX, s),
    "storage_path": lambda s: verify_accessible_path(Path(s)),
    "course_ids": lambda l: all(isinstance(i, int) for i in l) or l == [],
}

TUI_STYLE: Final[TuiStyle] = {
    "box": "DOUBLE",
    "width": 50,
}

LOGGING_CONFIG: Final[dict[str, Any]] = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "simple": {"format": "%(levelname)s: %(message)s"},
        "detailed": {
            "format": "[%(levelname)s|%(module)s|L%(lineno)d] %(asctime)s: %(message)s",
            "datefmt": "%Y-%m-%dT%H:%M:%S%z",
        },
    },
    "handlers": {
        "stderr": {
            "class": "logging.StreamHandler",
            "level": "WARNING",
            "formatter": "simple",
            "stream": "ext://sys.stderr",
        },
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "DEBUG",
            "formatter": "detailed",
            "filename": LOG_FN,
            "maxBytes": 10 * 1024**2,
            "backupCount": 3,
        },
    },
    "loggers": {"root": {"level": "DEBUG", "handlers": ["stderr", "file"]}},
}
