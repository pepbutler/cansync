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
    logging.config.dictConfig(LOGGING_CONFIG)


def short_name(name: str, max_length: int) -> str:
    """
    Convert a long name to a short version for pretty UI

    :returns: shorter course title
    """
    if len(name) < max_length:
        return name.ljust(max_length)
    else:
        return name[: max_length - 2] + ".."


def better_course_name(name: str) -> str:
    return re.sub(r" \((\d,? ?)+\)", "", name)


def create_dir(directory) -> None:
    """
    Create a new directory if it does not already exist

    :param directory: full path of directory to be made
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


def complete(config: ConfigDict) -> ConfigDict:
    """
    Validates config to check all fields are present (not necessarily valid)

    :returns: config that was given
    """
    if not CONFIG_KEY_DEFINITIONS.keys() == config.keys():
        first_missing_key = [
            v for k, v in CONFIG_KEY_DEFINITIONS.items() if k not in config.keys()
        ][0]
        e = f"No valid {first_missing_key} found in config file {CONFIG_FN} (Maybe delete it)"
        raise InvalidConfigurationError(e)
    else:
        return config


def valid(config: ConfigDict) -> ConfigDict:
    """
    Validates config to check all fields are valid and present
    """
    config = complete(config)
    e = ""

    if not re.match(URL_REGEX, config["url"]):
        e = "Invalid URL provided"

    if not re.match(API_KEY_REGEX, config["api_key"]):
        e = "Invalid API key format"

    if not isinstance(config["course_ids"], list):
        e = "Invalid course ID list"
    else:
        if not all(isinstance(id, int) for id in config["course_ids"]):
            e = "Invalid course ID values"

    if e:
        raise InvalidConfigurationError(e)
    else:
        return config


def get_config(invalid_ok: bool = False) -> ConfigDict:
    """
    Get config options from config file

    :returns: Config as a key-value dictionary
    """
    with open(CONFIG_FN, "r") as fp:
        logger.debug("Retrieving config from file")
        config = ConfigDict(**toml.load(fp))

    if not invalid_ok:
        check = valid(config)

    return config


def set_config(config: ConfigDict, partial_ok=False) -> None:
    """
    Write to local config file
    """
    if not partial_ok:
        config = complete(config)
    with open(CONFIG_FN, "w") as fp:
        logger.debug("Writing config")
        toml.dump(config, fp)


def overwrite_config_value(
    key: ConfigKeys,
    value: str | list[int],
    invalid_ok: bool = False,
    partial_ok: bool = False,
) -> None:
    """
    Overwrite a specific value in the config file
    """
    if key not in DEFAULT_CONFIG.keys():
        raise ValueError(f"Overwrite with non-existent key '{key}'")

    config = get_config(invalid_ok=invalid_ok)
    config[key] = value
    set_config(config, partial_ok)


def download_structured(file: File, *dirs: str, force=False, tui=False) -> bool:
    """
    Download a canvasapi File and preserve course structure in the form of directory
    names

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
                f"Tried to download {file.filename} but we don't have access"
            )
            return False
    else:
        logger.info(f"{file.filename} already present, skipping")
        return False
