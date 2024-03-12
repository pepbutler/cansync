import pytest

import cansync.utils as utils
from cansync.const import CONFIG_FN
from cansync.types import ConfigDict, ConfigKeys

import os
from typing import Final
from copy import copy


VALID_CONFIG: Final[ConfigDict] = {
    "url": "https://canvas.bham.ac.uk",
    "api_key": "1234~aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
    "course_ids": [123456, 234567, 345678],
}

INVALID_CONFIG: Final[ConfigDict] = {
    "url": "bruh",
    "api_key": "jfdkah8b298j2ifjkdhs92kfldh",
    "course_ids": ["j"],
}

PARTIAL_VALID_CONFIG: Final[ConfigDict] = copy(VALID_CONFIG)
PARTIAL_VALID_CONFIG.pop("api_key")

PARTIAL_INVALID_CONFIG: Final[ConfigDict] = copy(INVALID_CONFIG)
# PARTIAL_INVALID_CONFIG.pop("api_key")


def test_short_name():
    long = "Very Super Long Course Name (Longer now!!!)"
    assert "Ver.." == utils.short_name(long, 5)
    assert long == utils.short_name(long, len(long))


def test_course_name():
    long = "Brilliant Course (212381, 378182)"
    assert "Brilliant Course" == utils.better_course_name(long)

    long = "Brilliant Course (By Bob and John) (918212, )"
    assert "Brilliant Course (By Bob and John)" == utils.better_course_name(long)


@pytest.fixture
def normal_dir() -> str:
    dirname = "test_created_dir"
    utils.create_dir(dirname)
    yield dirname
    os.removedirs(dirname)


@pytest.fixture
def nested_dir() -> str:
    dirname = os.path.join("test_created_dir", "test2", "test3")
    penultimate = os.path.join("test_created_dir", "test2")
    utils.create_dir(dirname)
    yield dirname

    # dont remove base dir as this would screw up the other teardown above
    os.rmdir(dirname)
    os.rmdir(penultimate)


def test_create_dir(normal_dir, nested_dir):
    assert os.path.exists(normal_dir) and os.path.isdir(normal_dir)
    assert os.path.exists(nested_dir) and os.path.isdir(nested_dir)


@pytest.fixture
def config() -> bool:
    utils.create_config()
    yield True
    os.remove(CONFIG_FN)


def test_create_config(config):
    assert os.path.exists(CONFIG_FN) and os.path.isfile(CONFIG_FN)


def test_complete():
    assert utils.complete(VALID_CONFIG) and utils.complete(INVALID_CONFIG)


def test_valid():
    assert utils.valid(VALID_CONFIG)
    assert not utils.valid(INVALID_CONFIG)
    assert not utils.valid(PARTIAL_VALID_CONFIG)


def test_valid_key():
    for k, v in VALID_CONFIG.items():
        assert utils.valid_key(k, v)


def test_set_config(config):
    utils.set_config(VALID_CONFIG)
    assert utils.get_config() == VALID_CONFIG


def test_get_config(config):
    utils.set_config(VALID_CONFIG)
    assert utils.get_config() == VALID_CONFIG


def test_overwrite_config():
    utils.set_config(VALID_CONFIG)
    utils.overwrite_config_value(
        "course_ids",
        [
            999999,
        ],
    )
    assert utils.get_config()["course_ids"] == [
        999999,
    ]


def test_download(): ...
