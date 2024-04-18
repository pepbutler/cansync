from collections.abc import Callable

from pytermgui import Button, Window, WindowManager


class ErrorWindow(Window):
    """
    Show pesky little error window when user submits invalid config information
    """

    def __init__(
        self, context: WindowManager, *body: str, on_done: Callable | None = None
    ):
        self.context = context
        self.body = body
        self.return_button = Button("Return", onclick=on_done if on_done else self.back)

        super().__init__(*self.body, "", self.return_button)
        self.set_title("Warning ⚠")
        self.center()

    def back(self, _: Button) -> None:
        self.context.remove(self)
