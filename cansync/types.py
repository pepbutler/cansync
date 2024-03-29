from canvasapi.course import Course as Course
from canvasapi.module import Module as Module, ModuleItem as ModuleItem
from canvasapi.file import File as File
from canvasapi.page import Page as Page
from canvasapi.quiz import Quiz as Quiz

# idk this is like giving a monkey a machine gun
# from pydantic import BaseModel, ValidationError
# from pydantic.functional_validators import AfterValidator

from typing import TypedDict, NamedTuple, Literal

ConfigKeys = Literal["url", "api_key", "course_ids", "storage_path"]


class ConfigDict(TypedDict):
    url: str
    api_key: str
    course_ids: list[int]
    storage_path: str


class CourseInfo(NamedTuple):
    name: str
    id: int
