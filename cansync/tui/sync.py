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
import functools

from abc import ABC, abstractmethod
from typing import Iterable, Any, Final


logger = logging.getLogger(__name__)


class SyncWindow(Window):
    def __init__(self, context: WindowManager, canvas: Canvas):
        self.context = context
        self.canvas = canvas
        self.title = "Sync"
        self.sync_button = Button("Sync all", onclick=self.sync)
        self.exit_button = Button("  Exit  ", onclick=self.exit)
        super().__init__(self.sync_button, self.exit_button, **TUI_STYLE)

    def action(self, course: CourseScan, module: ModuleScan, action: str) -> None:
        super().__init__(
            Container(TUI_STRINGS["sync"].format(course.name, module.name, action)),
            self.sync_button,
            self.exit_button,
            **TUI_STYLE,
        )

    def finish(self) -> None:
        super().__init__("[bold accent]Done :bangbang:", self.exit_button)

    def sync(self, button: Button) -> None:

        for course in self.canvas.get_courses():

            for module in course.get_modules():

                for attachment in module.get_attachments():
                    self.action(course, module, "Downloading attachments...")
                    self.download(attachment, None, course, module)

                for page in module.get_pages():
                    self.action(course, module, f"Reading page...")

                    for file in page.get_files():
                        self.action(course, module, "Downloading file...")
                        self.download(file, page, course, module)

        self.finish()

    def download(
        self,
        file: File,
        page: PageScan | None,
        course: CourseScan,
        module: ModuleScan,
    ) -> None:
        logger.info(f"Downloading {file.filename}")
        if page is not None:
            new = utils.download_structured(file, course.name, module.name, page.name)
        else:
            new = utils.download_structured(file, course.name, module.name)

        if not new:
            self.action(course, module, "Skipping file...")

    def exit(self, _: Button) -> None:
        self.context.stop()


class SyncApplication:
    def __init__(self):
        self._manager = WindowManager()
        self.canvas = Canvas()

        if self.canvas.connect():
            self.main_window = SyncWindow(self._manager, self.canvas)
        else:
            from cansync.tui import ErrorWindow

            self.main_window = ErrorWindow(
                "You need to configure the settings before downloading stuff, try:",
                "",
                Container(f"cansync settings".center(64)),
            )

    def run(self, window: Window):
        with self._manager as manager:
            manager.add(window)

    def start(self):
        self.run(self.main_window)
