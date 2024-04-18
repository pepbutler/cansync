import requests
import logging.config
import toml
import os
import re
from functools import reduce
from pathlib import Path

from cansync.errors import InvalidConfigurationError
from cansync.types import ConfigDict, ConfigKeys, File, Iterable

from canvasapi.exceptions import ResourceDoesNotExist


logger = logging.getLogger(__name__)


def verify_accessible_path(p: Path) -> bool:
    """
    Test if the user can access a given path to prevent compounding
    files access errors
    """
    if p.exists():
        if p.owner() == os.getlogin():
            return True
        else:
            return False

    try:
        p.mkdir()
        return True
    except PermissionError as e:
        logger.warn(e)
        return False
    except Exception as e:
        logger.warn(f"Unknown path resolution error: '{e}'")
        return False


def setup_logging() -> None:
    """
    Setup logging using logging config defined in const.py
    """
    from cansync.const import LOGGING_CONFIG

    logging.config.dictConfig(LOGGING_CONFIG)


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
    logger.debug("Creating directory {} if not existing".format(directory))
    os.makedirs(directory, exist_ok=True)


def create_config() -> None:
    """Create config file when there is none present"""
    from cansync.const import CONFIG_DIR, CONFIG_FN, CONFIG_DEFAULTS

    if not CONFIG_FN.exists():
        logger.debug(f"Creating new config file at {CONFIG_FN}")
        os.makedirs(CONFIG_DIR, exist_ok=True)
        set_config(CONFIG_DEFAULTS)


def complete(config: ConfigDict) -> bool:
    """Check if all fields are present in the config, if not then it's probably broken"""
    from cansync.const import CONFIG_KEY_DEFINITIONS

    return CONFIG_KEY_DEFINITIONS.keys() == config.keys()


def valid_key(key: ConfigKeys, value: str | list[int]) -> bool:
    """Validates config key and value against test conditions"""
    from cansync.const import CONFIG_KEY_DEFINITIONS, CONFIG_VALIDATORS

    if key not in CONFIG_KEY_DEFINITIONS.keys():
        raise KeyError(f"Key '{key}' not in config definition")
    return CONFIG_VALIDATORS[key](value)


def valid(config: ConfigDict) -> bool:
    """
    Validates config to check all fields are correct and present

    :returns: If the config is deemed valid
    """
    k: ConfigKeys
    v: str | list[int]
    return all(valid_key(k, v) for k, v in config.items()) and complete(config)  # type: ignore[arg-type]


def get_config() -> ConfigDict:
    """
    Get config options from config file

    :returns: Config as a key-value dictionary
    """
    from cansync.const import CONFIG_FN

    with open(CONFIG_FN, "r") as fp:
        logger.debug("Retrieving config from file")
        config = ConfigDict(**toml.load(fp))  # type: ignore[typeddict-item]

    return config


def set_config(config: ConfigDict) -> None:
    """
    Write to local config file
    """
    from cansync.const import CONFIG_FN

    if not complete(config):
        raise InvalidConfigurationError(
            f"Some config keys are missing"
        )  # this is NOT helpful
    with open(CONFIG_FN, "w") as fp:
        logger.debug("Writing config")
        toml.dump(config, fp)


def overwrite_config_value(key: ConfigKeys, value: str | list[int]) -> None:
    """
    Overwrite a specific value in the config file
    """
    from cansync.const import CONFIG_DEFAULTS

    if key not in CONFIG_DEFAULTS.keys():
        raise InvalidConfigurationError(f"Overwrite with non-existent key '{key}'")

    config = get_config()
    config[key] = value
    set_config(config)


def download_structured(file: File, *dirs: str, force=False, tui=False) -> bool:
    """
    Download a canvasapi File and preserve course structure using directory names

    :returns: If the file was downloaded
    """
    download_dir = Path(get_config()["storage_path"])
    p: Path
    q: str

    # this is my favourite line of code (that mypy hates :D)
    path: Path = reduce(lambda p, q: p / q, [download_dir, *dirs])  # type: ignore[operator, assignment]
    file_path = path / file.filename
    create_dir(path)

    if not file_path.exists() or force:
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
