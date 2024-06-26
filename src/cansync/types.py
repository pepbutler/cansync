from enum import StrEnum
from typing import Literal, NamedTuple, TypedDict

from canvasapi.course import Course as Course
from canvasapi.file import File as File
from canvasapi.module import Module as Module
from canvasapi.module import ModuleItem as ModuleItem
from canvasapi.page import Page as Page
from canvasapi.quiz import Quiz as Quiz

ConfigKeys = Literal["url", "api_key", "course_ids", "storage_path"]


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


class ConfigDict(TypedDict):
    url: str
    api_key: str
    course_ids: list[int]
    storage_path: str


class CourseInfo(NamedTuple):
    name: str
    id: int


class TuiStyle(TypedDict):
    box: str
    width: int
