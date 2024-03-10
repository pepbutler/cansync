from __future__ import annotations

import cansync.utils as utils
from cansync.types import File, Module, ModuleItem, Course, Page, CourseInfo

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Callable, Optional, Generator, Any

import re
import logging
import canvasapi
from canvasapi.exceptions import InvalidAccessToken
from requests.exceptions import MissingSchema


logger = logging.getLogger(__name__)


class Canvas:
    """
    Library version of canvasapi.Canvas that exposes only used methods and information
    and avoids putting canvasapi stuff everywhere while utilizing the config
    """

    def __init__(self):
        self._canvas = None

        # self.connect()
        #

    def load_config(self) -> None:
        config = utils.get_config()
        self.url = config["url"]
        self.api_key = config["api_key"]
        self.course_ids = config["course_ids"]

    def connect(self) -> bool:
        logger.info("Starting canvasapi.Canvas instance")
        try:
            self.load_config()
            self._canvas = canvasapi.Canvas(self.url, self.api_key)
            self._canvas.get_current_user()  # test request
            return True
        except (
            InvalidAccessToken,
            MissingSchema,
        ) as e:  # i expect more errors cropping up
            self._canvas = None
            logger.warn(e)
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
        return CourseScan.load(self._canvas.get_course(id), self)

    def get_courses_info(self) -> Generator[CourseInfo, None, None]:
        courses = self._canvas.get_courses()
        for course in courses:
            yield CourseInfo(course.name, course.id)


class Scanner(ABC):
    """
    Define an interface to aid in standardizing what data is available
    """

    canvas: Canvas
    course: CourseScan

    @staticmethod
    @abstractmethod
    def load(item: Any, *args, **kwargs) -> Scanner: ...

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

    @staticmethod
    def load(course: Course, canvas: Canvas) -> CourseScan:
        return CourseScan(
            course,
            canvas,
        )

    @property
    def name(self) -> str:
        return utils.better_course_name(self.course.name)

    @property
    def id(self) -> int:
        return self.course.id

    @property
    def file_regex(self) -> str:
        return r"{}/courses/{}/files/([0-9]+)".format(self.canvas.url, self.id)

    @property
    def code(self) -> str:
        return self.course.code

    def get_modules(self) -> Generator[ModuleScan, None, None]:
        for module in self.course.get_modules():
            yield ModuleScan.load(module, self.canvas, self)


# TODO: add quizez
@dataclass
class ModuleScan(Scanner):
    """
    Modules on canvas that provide pages and attachments although more types of items
    can be added
    """

    module: Module
    course: CourseScan
    canvas: Canvas

    @staticmethod
    def load(module: Module, canvas: Canvas, course: CourseScan) -> ModuleScan:
        return ModuleScan(module, course, canvas)

    @property
    def name(self) -> str:
        return self.module.name

    @property
    def id(self) -> int:
        return self.module.id

    def get_pages(self) -> Generator[PageScan, None, None]:
        for item in self.module.get_module_items():
            if hasattr(item, "page_url"):
                yield PageScan.load(
                    self.course._course.get_page(item.page_url),
                    self.canvas,
                    self.course,
                )

    def get_attachments(self) -> Generator[File, None, None]:
        for item in self.module.get_module_items():
            if hasattr(item, "url"):
                if re.match(self.course.file_regex, item.url):
                    yield self.canvas.get_file(int(item.url.split("/")[-1]))


# TODO: add images, files, text
@dataclass
class PageScan(Scanner):
    """
    Pages on canvas that provide some scrapable file links a long with other items at
    the discretion of the course director
    """

    page: Page
    course: Course
    canvas: Canvas

    @staticmethod
    def load(page: Page, canvas: Canvas, course: CourseScan) -> PageScan:
        return PageScan(page, course, canvas)

    @property
    def name(self) -> str:
        return self.page.title

    @property
    def id(self) -> int:
        return self.page.id

    @property
    def empty(self) -> bool:
        if not hasattr(self.page, "body"):
            logger.debug(
                f"Page with id {self.id} has no body"
            )  # its pretty weird ennit
            return True
        else:
            return self.page.body is None

    def get_files(self) -> Generator[File, None, None]:
        if self.empty:
            return

        found_file_ids = re.findall(self.course.file_regex, self.page.body)

        for id in found_file_ids:
            if id is not None:
                yield self.canvas.get_file(id)
