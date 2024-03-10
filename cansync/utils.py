import requests
import logging.config
import toml
import os
import re

from urllib.parse import urlparse

from cansync.const import (
    DOWNLOAD_DIR,
    CONFIG_DIR,
    CONFIG_FN,
    DEFAULT_CONFIG,
    CONFIG_KEY_DEFINITIONS,
    CONFIG_VALIDATORS,
    URL_REGEX,
    API_KEY_REGEX,
    LOGGING_CONFIG,
)
from cansync.errors import InvalidConfigurationError
from cansync.types import ConfigDict, ConfigKeys, File

from canvasapi.exceptions import ResourceDoesNotExist


logger = logging.getLogger(__name__)

# TODO: remove the curse


def setup_logging() -> None:
    """
    Setup logging using logging config defined in config.py
    """
    logging.config.dictConfig(LOGGING_CONFIG)


def short_name(name: str, max_length: int) -> str:
    """
    Convert a long name to a short version for pretty UI

    :returns: Shorter course title
    """
    if len(name) < max_length:
        return name.ljust(max_length)
    else:
        return name[: max_length - 2] + ".."


def better_course_name(name: str) -> str:
    """
    Removes ID numbers next to the given title of the course

    :returns: Course name
    """
    return re.sub(r" \((\d,? ?)+\)", "", name)


def create_dir(directory: str) -> None:
    """
    Create a new directory if it does not already exist

    :param directory: Full path of directory to be made
    """
    logger.debug("Creating directory {} if not existing".format(directory))
    os.makedirs(directory, exist_ok=True)


def create_config() -> None:
    """
    Create config file when there is none present
    """
    if not os.path.exists(CONFIG_FN):
        logger.debug(f"Creating new config file at {CONFIG_FN}")
        os.makedirs(CONFIG_DIR, exist_ok=True)
        set_config(DEFAULT_CONFIG)


def complete(config: ConfigDict) -> bool:
    """
    Validates config to check all fields are present (not necessarily valid)

    :returns: If the config given is complete
    """
    return CONFIG_KEY_DEFINITIONS.keys() == config.keys()


def valid(config: ConfigDict) -> bool:
    """
    Validates config to check all fields are valid and present

    :returns: If the config is deemed valid
    """
    assert complete(config), "Fields are missing from the config file"
    return all(CONFIG_VALIDATORS[k](v) for k, v in config.items())


def valid_key(key: ConfigKeys, value: str | list[int]) -> bool:
    """
    Validates config key and value against valid conditions

    :returns: If the particular key and value is deemed valid
    """
    if key not in CONFIG_KEY_DEFINITIONS.keys():
        raise KeyError(f"Key '{key}' not in config definition")
    return CONFIG_VALIDATORS[key](value)


def get_config() -> ConfigDict:
    """
    Get config options from config file

    :returns: Config as a key-value dictionary
    """
    with open(CONFIG_FN, "r") as fp:
        logger.debug("Retrieving config from file")
        config = ConfigDict(**toml.load(fp))

    return config


def set_config(config: ConfigDict) -> None:
    """
    Write to local config file
    """
    if not complete(config):
        raise InvalidConfigurationError()
    with open(CONFIG_FN, "w") as fp:
        logger.debug("Writing config")
        toml.dump(config, fp)


def overwrite_config_value(key: ConfigKeys, value: str | list[int]) -> None:
    """
    Overwrite a specific value in the config file
    """
    if key not in DEFAULT_CONFIG.keys():
        raise ValueError(f"Overwrite with non-existent key '{key}'")

    config = get_config()
    config[key] = value
    set_config(config)


def download_structured(file: File, *dirs: str, force=False, tui=False) -> bool:
    """
    Download a canvasapi File and preserve course structure using directory names

    :returns: If the file was downloaded
    """
    path = os.path.join(DOWNLOAD_DIR, *dirs)
    fpath = os.path.join(path, file.filename)
    create_dir(path)

    if not os.path.exists(fpath) or force:
        logger.info(f"Downloading {file.filename}" + "" if not force else " (forced)")
        try:
            file.download(fpath)
            return True
        except ResourceDoesNotExist as e:
            logger.warning(
                f"Tried to download {file.filename} but we likely don't have access"
            )
            return False
    else:
        logger.info(f"{file.filename} already present, skipping")
        return False
