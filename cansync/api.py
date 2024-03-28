from __future__ import annotations

import cansync.utils as utils
from cansync.types import File, Module, ModuleItem, Course, Page, CourseInfo, Quiz
from cansync.const import ModuleItemType

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Callable, Optional, Generator, Any

import re
import logging
import canvasapi
from functools import cached_property

from canvasapi.exceptions import InvalidAccessToken, ResourceDoesNotExist
from requests.exceptions import MissingSchema


logger = logging.getLogger(__name__)


class Canvas:
    """
    Library version of canvasapi.Canvas that exposes only used methods and information
    and avoids putting canvasapi stuff everywhere while utilizing the config.

    Canvas objects do *not* connect by default because the thing might not be configured
    correctly yet.
    """

    def __init__(self):
        self._canvas = None

        config = utils.get_config()
        self.url = config["url"]
        self.api_key = config["api_key"]
        self.course_ids = config["course_ids"]

    def reload_config(self) -> None:
        config = utils.get_config()
        self.url = config["url"]
        self.api_key = config["api_key"]

    def connect(self) -> bool:
        logger.info("Starting canvasapi.Canvas instance")
        try:
            self.reload_config()
            self._canvas = canvasapi.Canvas(self.url, self.api_key)
            self._canvas.get_current_user()  # test request
            return True
        except (InvalidAccessToken, MissingSchema, ResourceDoesNotExist) as e:
            self._canvas = None
            logger.warning(e)
            return False

    @property
    def connected(self) -> bool:
        return self._canvas is not None

    def get_file(self, id: int) -> File:
        return self._canvas.get_file(id)

    def get_courses(self) -> Generator[CourseScan, None, None]:
        for id in self.course_ids:
            yield self.get_course(id)

    def get_course(self, id: int) -> CourseScan:
        return CourseScan(self._canvas.get_course(id), self)

    def get_courses_info(self) -> Generator[CourseInfo, None, None]:
        courses = self._canvas.get_courses()
        for course in courses:
            yield CourseInfo(course.name, course.id)

    def get_quiz(self, id: int) -> Generator[Quiz, None, None]:
        return self._canvas.get_quiz(id)


class Scanner(ABC):
    """
    Define an interface to aid in standardizing what data is available
    from any canvas object
    """

    canvas: Canvas
    course: CourseScan

    @property
    @abstractmethod
    def name(self) -> str: ...

    @property
    @abstractmethod
    def id(self) -> int: ...


@dataclass
class CourseScan(Scanner):
    """
    Courses on canvas that provide modules
    """

    course: Course
    canvas: Canvas

    @property
    def name(self) -> str:
        return utils.better_course_name(self.course.name)

    @property
    def id(self) -> int:
        return self.course.id

    @property
    def code(self) -> str:
        return self.course.code

    @property
    def resource_regex(self) -> str:
        return rf"{self.canvas.url}/(api/v1/)?courses/{self.id}/{{}}/([0-9]+)"

    def get_modules(self) -> Generator[ModuleScan, None, None]:
        for module in self.course.get_modules():
            yield ModuleScan(module, self, self.canvas)

    def get_page(self, url: str) -> Page:
        return self.course.get_page(url)


@dataclass
class ModuleScan(Scanner):
    """
    Modules on canvas that provide pages and attachments although more types of items
    can be added
    """

    module: Module
    course: CourseScan
    canvas: Canvas

    @property
    def name(self) -> str:
        return self.module.name

    @property
    def id(self) -> int:
        return self.module.id

    @cached_property
    def items(self) -> list[ModuleItem]:
        return [item for item in self.module.get_module_items()]

    def items_by_type(self, type: ModuleItemType) -> Generator[ModuleItem, None, None]:
        yield from filter(lambda item: ModuleItemType(item.type) is type, self.items)

    def get_pages(self) -> Generator[PageScan, None, None]:
        for item in self.items_by_type(ModuleItemType.PAGE):
            yield PageScan(
                self.course.get_page(item.page_url),
                self.course,
                self.canvas,
            )

    def get_attachments(self) -> Generator[File, None, None]:
        for item in self.items_by_type(ModuleItemType.ATTACHMENT):
            yield self.canvas.get_file(item.content_id)

    def get_quizzes(self) -> Generator[Quiz, None, None]:
        for item in self.items_by_type(ModuleItemType.QUIZ):
            yield self.canvas.get_quiz(item.content_id)


@dataclass
class PageScan(Scanner):
    """
    Pages on canvas that provide some scrapable file links a long with other items at
    the discretion of the course director
    """

    page: Page
    course: CourseScan
    canvas: Canvas

    @property
    def name(self) -> str:
        return self.page.title

    @property
    def id(self) -> int:
        return self.page.page_id

    @property
    def empty(self) -> bool:
        # Prevent attribute errors
        if not hasattr(self.page, "body"):
            logger.debug(f"Page with id {self.id} has no body")
            return True
        else:
            return self.page.body is None

    def _scan_body(self, resource: str, getter: Callable) -> Any:
        if self.empty:
            return

        for _, id in re.findall(
            self.course.resource_regex.format(resource), self.page.body
        ):
            logger.info(f"Scanned {resource}({id}) from Page({self.id})")
            if id is not None:
                yield getter(id)

    def get_files(self) -> Generator[File, None, None]:
        yield from self._scan_body("files", self.canvas.get_file)

    def get_quizzes(self) -> Generator[Quiz, None, None]:
        yield from self._scan_body("quizzes", self.canvas.get_quiz)
