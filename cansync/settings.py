from cansync.const import TUI_STRINGS, DEFAULT_CONFIG, ANNOYING_MSG, TUI_STYLE
from cansync.api import Canvas
from cansync.types import CourseInfo
from cansync.errors import InvalidConfigurationError
import cansync.utils as utils

from pytermgui import (
    WindowManager,
    Window,
    Button,
    InputField,
    Container,
    Splitter,
)

import re
import time

from typing import Callable, Any, Generator, Optional, Literal


class AnnoyingExitWindow(Window):
    """
    Show pesky little error window when user submits invalid config information
    """

    def __init__(self, context: WindowManager, body: str):
        self.context = context
        self.ok_button = Button("Exit", onclick=self.exit)
        self.return_button = Button("Return", onclick=self.back)
        self.options = Splitter(self.ok_button, self.return_button)
        super().__init__(body, "", self.options, **TUI_STYLE)

        self.set_title("⚠ Warning ⚠")
        self.center()
        self.move(10, 10)

    def exit(self, _: Button) -> None:
        self.context.remove(self)
        self.context.stop()
        exit(1)

    def back(self, _: Button) -> None:
        self.context.remove(self)


# TODO: Clean this shit up
class SelectWindow(Window):
    """
    User can select an operation to perform which modifies some settings
    """

    settings = {
        "width": 29,
    }

    def __init__(
        self,
        context: WindowManager,
        on_click: Callable,
        exclude_course_select: bool = False,
    ):
        self.context = context

        if exclude_course_select:
            strings = TUI_STRINGS["select"][:-1]
        else:
            strings = TUI_STRINGS["select"]

        max_length = max(len(s) for s in strings)
        opts = [o.ljust(max_length) for o in strings]
        buttons_container = Container(
            *[Button(o, onclick=on_click, centered=True) for o in opts]
        )
        exit_container = Container(Button("Done", onclick=self.exit, centered=True))

        super().__init__(
            buttons_container,
            exit_container,
            **self.settings,
        )
        self.set_title("Settings")
        self.center()

    def exit(self, _: Button) -> None:
        try:
            config = utils.get_config()
            self.context.stop()
            exit(0)
        except InvalidConfigurationError as e:
            self.context.add(AnnoyingExitWindow(self.context, ANNOYING_MSG))


class ConfigEditWindow(Window):
    """
    Edit a specific config value via the input field
    """

    def __init__(
        self,
        context: WindowManager,
        title: str,
        prompt: str,
        submit_callback: Callable,
        **settings: str | int | bool,
    ):
        self.input_field = InputField("", prompt=prompt)
        self.context = context

        submit_container = Splitter(
            Button("Submit", onclick=self._input_on_submit_callback(submit_callback)),
            Button("Cancel", onclick=self.on_cancel),
        )

        super().__init__(
            f"[bold accent]{title}",
            self.input_field,
            "",
            submit_container,
            **settings,
        )

        self.center()

    def on_cancel(self, _: Button) -> None:
        """
        Cancel button
        """
        self.exit()

    def _input_on_submit_callback(self, callback: Callable) -> Callable[[Button], Any]:
        """
        Provides the callback function the input field text as an argument instead of
        the submit button object (discarding it)

        :returns: Wrapped callback function
        """

        def callback_with_input(_: Button) -> Any:
            return callback(self.input_field.value.rstrip())

        return callback_with_input

    def _overwrite_value(
        self, text: str, key: Literal["url", "api_key", "course_ids"]
    ) -> None:
        if key not in DEFAULT_CONFIG.keys():
            raise ValueError(f"Non-existent config key {key}")

        config = utils.get_config(invalid_ok=True)
        config[key] = text
        utils.overwrite_config_value(key, text, invalid_ok=True, partial_ok=True)
        self.exit()

    def exit(self):
        self.context.remove(self)


class URLTypeWindow(ConfigEditWindow):
    """
    Window for configuring the Canvas URL
    """

    def __init__(self, context: WindowManager):
        super().__init__(context, *TUI_STRINGS["url"], self.on_submit, width=60)

    def on_submit(self, text: str):
        self._overwrite_value(text.strip("/"), "url")


class APIKeyTypeWindow(ConfigEditWindow):
    """
    Window for configuring the API key
    """

    def __init__(self, context: WindowManager):
        super().__init__(context, *TUI_STRINGS["api"], self.on_submit, width=79)

    def on_submit(self, text: str):
        self._overwrite_value(text, "api_key")


class CoursesWindow(Window):
    """
    Show a list of courses as checkboxes and append select courses' ids to the config
    file
    """

    def __init__(self, context: WindowManager, canvas: Canvas):
        self.context = context
        self.course_id: dict[CourseInfo] = {}
        self.canvas = canvas

        self.enabled = Container()
        self.disabled = Container()
        self.submit = Container(Button("Submit", onclick=self.on_submit, centered=True))

        super().__init__(
            "[bold]Disabled",
            "",
            self.disabled,
            "[bold]Enabled",
            "",
            self.enabled,
            self.submit,
            **TUI_STYLE,
        )

        self.center()

        for name, id in self.canvas.get_courses_info():
            max_length = TUI_STYLE["width"] - 14
            shortened_name = utils.short_name(name, max_length)

            self.course_id[shortened_name] = id
            course_button = Button(shortened_name, onclick=self.on_button_click)
            self.disabled += course_button
            self.height += 1

    def on_button_click(self, button: Button) -> None:
        def swap_container(button: Button, con1: Container, con2: Container) -> None:
            """
            Swap button from con1 -> con2 AND retain selection position
            """
            idx = con1._widgets.index(button)

            con1.remove(button)
            con2 += button

            if idx > 0:
                con1.select(idx)

        if button in self.disabled:
            swap_container(button, self.disabled, self.enabled)
        elif button in self.enabled:
            swap_container(button, self.enabled, self.disabled)

    def on_submit(self, _: Button) -> None:
        utils.overwrite_config_value(
            "course_ids",
            [self.course_id[b.label] for b in self.enabled],
        )
        self.exit()

    def exit(self):
        self.context.remove(self)


class SettingsApplication:
    """
    TUI application to manage settings easily
    """

    def __init__(self, canvas: Canvas | None = None):
        self._manager = WindowManager()
        self._main_window = SelectWindow(
            self._manager,
            self.on_select_button_click,
            exclude_course_select=bool(canvas is None),
        )
        self._url_window = URLTypeWindow(self._manager)
        self._api_key_window = APIKeyTypeWindow(self._manager)

        if canvas is not None:
            self._courses_window = CoursesWindow(self._manager, canvas)
        else:
            self._courses_window = Window()

    def on_select_button_click(self, button: Button) -> None:
        """
        Select menu chooses which window to open
        """

        label = button.label.rstrip()
        url, api, course = TUI_STRINGS["select"]

        if label == url:
            self.run(self._url_window)
        if label == api:
            self.run(self._api_key_window)
        if label == course:
            self.run(self._courses_window)

    def stop(self) -> None:
        self._manager.stop()

    def run(self, window: Window) -> None:
        with self._manager as manager:
            manager.add(window)

    def start(self) -> None:
        self.run(self._main_window)
