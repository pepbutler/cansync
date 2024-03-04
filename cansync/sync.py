from __future__ import annotations
from cansync.api import Canvas, CourseScan, ModuleScan, PageScan, Scanner
from cansync.const import DOWNLOAD_DIR, TUI_STYLE, TUI_STRINGS
from cansync.types import File, Course, Module, ModuleItem, Page
import cansync.utils as utils

from canvasapi.exceptions import ResourceDoesNotExist

from pytermgui import (
    Window,
    WindowManager,
    Container,
    Button,
    InputField,
    Splitter,
    Label,
)

import os
import logging
import threading
import functools

from abc import ABC, abstractmethod
from typing import Iterable, Any, Final


CONTAINER_STR: Final[
    str
] = """
Course: {}
Module: {}
[bold accent]{}
"""


class SyncWindow(Window):
    def __init__(self, context: WindowManager, canvas: Canvas):
        self.context = context
        self.canvas = canvas
        self.title = "Sync"
        self.sync_button = Button("Sync all", onclick=self.sync)
        self.exit_button = Button("  Exit  ", onclick=self.exit)
        super().__init__(self.sync_button, self.exit_button, **TUI_STYLE)

    def show_action(self, course: CourseScan, module: ModuleScan, action: str) -> None:
        super().__init__(
            Container(CONTAINER_STR.format(course.name, module.name, action)),
            self.sync_button,
            self.exit_button,
            **TUI_STYLE,
        )

    def show_done(self) -> None:
        super().__init__("[bold accent]D o n e", self.exit_button)

    def sync(self, button: Button) -> None:

        for course in self.canvas.get_courses():

            for module in course.get_modules():

                for attachment in module.get_attachments():
                    self.show_action(course, module, "Downloading attachments...")
                    self.download(attachment, None, course, module)

                for page in module.get_pages():
                    self.show_action(course, module, f"Reading page...")

                    for file in page.get_files():
                        self.show_action(course, module, "Downloading file...")
                        self.download(file, page, course, module)

        self.show_done()

    def download(
        self,
        file: File,
        page: PageScan | None,
        course: CourseScan,
        module: ModuleScan,
    ) -> None:
        if page is not None:
            new = utils.download_structured(file, course.name, module.name, page.name)
        else:
            new = utils.download_structured(file, course.name, module.name)

        if not new:
            self.show_action(course, module, "Skipping file...")

    def exit(self, _: Button) -> None:
        self.context.stop()


class SyncApplication:
    def __init__(self, canvas: Canvas):
        self._manager = WindowManager()
        self.main_window = SyncWindow(self._manager, canvas)

    def run(self, window: Window):
        with self._manager as manager:
            manager.add(window)

    def start(self):
        self.run(self.main_window)
