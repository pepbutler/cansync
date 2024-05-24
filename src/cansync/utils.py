import logging.config
import os
import re
from functools import reduce
from pathlib import Path

import toml
from canvasapi.exceptions import ResourceDoesNotExist

from cansync.errors import InvalidConfigurationError
from cansync.types import ConfigDict, ConfigKeys, File

logger = logging.getLogger(__name__)


def verify_accessible_path(p: Path) -> bool:
    """
    Test if the user can access a given path to prevent compounding
    files access errors
    """
    if p.exists():
        return p.owner() == os.getlogin()

    try:
        p.mkdir(parents=True)
        return True
    except PermissionError as e:
        logger.warn(e)
        return False
    except Exception as e:
        logger.warn(f"Unknown path resolution error: '{e}'")
        return False


def setup_logging() -> None:
    """Setup logging using logging config defined in const.py"""
    from cansync.const import LOGGING_CONFIG

    logging.config.dictConfig(LOGGING_CONFIG)


def path_format(name: str) -> str:
    return name.replace(" ", "-")


def short_name(name: str, max_length: int) -> str:
    """Convert a long name to a short version for pretty UI"""
    if len(name) <= max_length:
        return name.ljust(max_length)
    else:
        return name[: max_length - 2] + ".."


def same_length(*strings: str) -> list[str]:
    """
    Extends short_name to apply to all strings in a list with the max
    length set to that of the largest string
    """
    from cansync.utils import short_name

    return [short_name(s, len(max(strings, key=lambda s: len(s)))) for s in strings]


def better_course_name(name: str) -> str:
    """Removes ID numbers next to the given title of the course"""
    return re.sub(r" \((\d,? ?)+\)", "", name)


def create_dir(directory: Path) -> None:
    """Create a new directory if it does not already exist"""
    logger.debug(f"Creating directory {directory} if not existing")
    os.makedirs(directory, exist_ok=True)


def create_config(config_path: Path | None = None) -> None:
    """Create config file when there is none present"""
    from cansync.const import CONFIG_DEFAULTS, CONFIG_PATH

    config_path = config_path if config_path else CONFIG_PATH

    if not config_path.exists():
        logger.debug(f"Creating new config file at {config_path}")
        create_dir(config_path.parent)
        set_config(CONFIG_DEFAULTS, config_path)


def complete(config: ConfigDict) -> bool:
    """
    Check if all fields are present in the config, if not then it's
    probably broken
    """
    from cansync.const import CONFIG_KEY_DEFINITIONS

    return CONFIG_KEY_DEFINITIONS.keys() == config.keys()


def valid_key(key: ConfigKeys, value: str | list[int]) -> bool:
    """Validates config key and value against test conditions"""
    from cansync.const import CONFIG_KEY_DEFINITIONS, CONFIG_VALIDATORS

    if key not in CONFIG_KEY_DEFINITIONS:
        e = f"Key '{key}' not in config definition"
        raise KeyError(e)
    return CONFIG_VALIDATORS[key](value)


def valid(config: ConfigDict) -> bool:
    """Validates config to check all fields are correct and present"""
    return all(valid_key(k, v) for k, v in config.items()) and complete(config)  # type: ignore[arg-type]


def get_config(path: Path | None = None) -> ConfigDict:
    """
    Get config options from config file

    :returns: Config as a key-value dictionary
    """
    from cansync.const import CONFIG_PATH

    with open(CONFIG_PATH) as fp:
        logger.debug("Retrieving config from file")
        config = ConfigDict(**toml.load(fp))  # type: ignore[typeddict-item]

    return config


def set_config(config: ConfigDict, dest: Path | None = None) -> None:
    """Write to local config file"""
    from cansync.const import CONFIG_PATH

    dest = dest if dest else CONFIG_PATH
    if not complete(config):
        e = "Some config keys are missing"
        raise InvalidConfigurationError(e)
    with open(dest, "w") as fp:
        logger.debug("Writing config")
        toml.dump(config, fp)


def overwrite_config_value(key: ConfigKeys, value: str | list[int]) -> None:
    """Overwrite a specific value in the config file"""
    from cansync.const import CONFIG_DEFAULTS

    if key not in CONFIG_DEFAULTS:
        e = f"Overwrite with non-existent key '{key}'"
        raise InvalidConfigurationError(e)

    config = get_config()
    config[key] = value
    set_config(config)


def download_structured(file: File, *dirs: str, force=False, tui=False) -> bool:
    """
    Download a canvasapi File and preserve course structure using directory names

    :returns: If the file was downloaded
    """
    download_dir = Path(get_config()["storage_path"]).expanduser()

    # this is my favourite line of code (that mypy hates :D)
    path: Path = reduce(lambda p, q: p / q, [download_dir, *dirs])  # type: ignore[operator, assignment]
    file_path = path / file.filename
    create_dir(path)

    if not file_path.is_file() or force:
        logger.info(f"Downloading {file.filename}" + "" if not force else " (forced)")
        try:
            file.download(file_path)
            return True
        except ResourceDoesNotExist as e:
            logger.warning(
                f"Tried to download {file.filename} but we likely don't have access ({e})"
            )
            return False
    else:
        logger.info(f"{file.filename} already present, skipping")
        return False
