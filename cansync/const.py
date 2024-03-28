import os
import re
from pathlib import Path
from enum import StrEnum

from typing import Final, Any, Callable
from cansync.types import ConfigDict


def _same_length(*strings: str) -> list[str]:
    from cansync.utils import short_name

    return [short_name(s, len(max(strings, key=len))) for s in strings]


class ModuleItemType(StrEnum):
    # INFO: https://canvas.instructure.com/doc/api/modules.html#ModuleItem
    HEADER = "SubHeader"
    PAGE = "Page"
    QUIZ = "Quiz"
    EXTERNAL_TOOL = "ExternalTool"
    EXTERNAL_URL = "ExternalUrl"
    ATTACHMENT = "File"
    DISCUSSION = "Discussion"
    ASSIGNMENT = "Assignment"


ANNOYING_MSG: Final[str] = "Incorrectly typed value!"
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

CONFIG_DIR: Final[Path] = XDG_CONFIG_DIR / "cansync"
CONFIG_FN: Final[Path] = CONFIG_DIR / "config.toml"
DEFAULT_CONFIG: Final[ConfigDict] = {
    "url": "",
    "api_key": "",
    "course_ids": [],
}
CONFIG_KEY_DEFINITIONS: Final[dict[str, str]] = {
    "url": "Canvas URL",
    "api_key": "API key",
    "course_ids": "course ID number(s)",
}
CONFIG_VALIDATORS: Final[dict[str, Callable]] = {
    "url": lambda s: re.match(URL_REGEX, s),
    "api_key": lambda s: re.match(API_KEY_REGEX, s),
    "course_ids": lambda l: all(isinstance(i, int) for i in l) or l == [],
}

CACHE_DIR: Final[Path] = XDG_CACHE_DIR / "cansync"
LOGFILE: Final[Path] = CACHE_DIR / "cansync.log"
DOCUMENTS_DIR: Final[Path] = HOME / "Documents"
DOWNLOAD_DIR: Final[Path] = DOCUMENTS_DIR / "Cansync"

TUI_STRINGS: Final[dict[str, list[str]]] = {
    "select_opts": _same_length(
        "Change Canvas URL", "Change API key", "Select courses"
    ),
    "url": ("Enter a Canvas URL", "Canvas URL: "),
    "api": ("Enter an API key", "Key: "),
    "sync": """
Course: {}
Module: {}
[bold accent]{}
""",
}

TUI_STYLE: Final[dict[str, str | int]] = {
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
            "filename": LOGFILE,
            "maxBytes": 10 * 1024**2,
            "backupCount": 3,
        },
    },
    "loggers": {"root": {"level": "DEBUG", "handlers": ["stderr", "file"]}},
}
