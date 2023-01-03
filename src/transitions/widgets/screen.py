import io
import asyncio
from dataclasses import dataclass

from rich.console import Console
from rich.text import Text
from textual import log
from textual.screen import Screen
from textual.widget import Widget
from textual.widgets import Static
from textual.containers import Vertical
from textual.app import ComposeResult
from textual.reactive import reactive


@dataclass
class ScreenInfo:
    size: tuple[int, int]
    content: str


class TransitionContainer(Widget):
    DEFAULT_CSS = """
    Screen TransitionContainer {
        height: 100%;
        width: 100%;
        layout: vertical;
        overflow: hidden;
    }
    """
    transition_offset = reactive(0.0)

    def __init__(self, from_screen, to_screen, transition):
        self.transition = transition
        self.from_screen_info = from_screen
        self.to_screen_info = to_screen
        self.from_screen = Text.from_ansi(from_screen.content)
        self.to_screen = Text.from_ansi(to_screen.content)
        self.width = self.from_screen_info.size[0]
        self.height = self.from_screen_info.size[1]
        super().__init__()

    def get_content_height(self, container, viewport, width: int) -> int:
        return self.from_screen_info.size[1]

    def get_content_width(self, container, viewport) -> int:
        return self.from_screen_info.size[0]

    def __rich_console__(self, console, options):
        match self.transition:
            case "slideover_up":
                lines = self.from_screen.split()[
                    0 : self.height - round(self.transition_offset)
                ]
                lines.extend(self.to_screen.split()[0 : round(self.transition_offset)])

                yield from lines
            case "wipe_up":
                lines = self.from_screen.split()[
                    0 : self.height - round(self.transition_offset)
                ]
                lines.extend(
                    self.to_screen.split()[
                        self.height - round(self.transition_offset) : self.height
                    ]
                )
                yield from lines
            case "slide_up":
                lines = self.from_screen.split()
                lines.extend(self.to_screen.split())

                yield from lines[
                    round(self.transition_offset) : round(self.transition_offset)
                    + self.height
                ]
            case "slideover_down":
                lines = self.to_screen.split()[
                    self.height - round(self.transition_offset) : self.height
                ]

                lines.extend(
                    self.from_screen.split()[
                        round(self.transition_offset) : self.height
                    ]
                )

                yield from lines
            case "slide_down":
                lines = self.to_screen.split()
                lines.extend(self.from_screen.split())

                offset = (-1 * round(self.transition_offset)) + self.height

                yield from lines[offset : offset + self.height]
            case "wipe_down":
                lines = self.to_screen.split()[0 : round(self.transition_offset)]
                lines.extend(
                    self.from_screen.split()[
                        round(self.transition_offset) : self.height
                    ]
                )

                yield from lines
            case "slide_left":
                from_columns = [
                    x[round(self.transition_offset) : self.width]
                    for x in self.from_screen.split()
                ]
                to_columns = [
                    x[0 : round(self.transition_offset)] for x in self.to_screen.split()
                ]

                for (from_line, to_line) in zip(from_columns, to_columns):
                    yield Text("").join([from_line, to_line])
            case "slide_right":
                from_columns = [
                    x[0 : self.width - round(self.transition_offset) - 1]
                    for x in self.from_screen.split()
                ]
                to_columns = [
                    x[self.width - 1 - round(self.transition_offset) : self.width]
                    for x in self.to_screen.split()
                ]

                for lines in zip(to_columns, from_columns):
                    yield Text("").join(lines)

    def render(self):
        return self


class TransitionScreen(Screen):

    DEFAULT_CSS = """
    Screen TransitionScreen, TransitionScreen {
        layout: vertical;
    }
    TransitionScreen TransitionContainer {
        layout: vertical;
        width: 100%;
    }
    """

    def __init__(self, transition, from_screen, to_screen):
        self.from_screen = from_screen
        self.to_screen = to_screen
        self.transition = transition
        super().__init__()

    def compose(self) -> ComposeResult:
        self.container = TransitionContainer(
            self.from_screen, self.to_screen, transition=self.transition
        )
        yield self.container

    def finish_transition(self):
        self.app.pop_screen()

    def on_show(self, event) -> None:
        delay = 2
        match self.transition:
            case "slide_up" | "slide_down":
                self.container.animate(
                    "transition_offset",
                    self.from_screen.size[1],
                    duration=delay,
                    on_complete=self.finish_transition,
                )
            case "slide_left" | "slide_right":
                self.container.animate(
                    "transition_offset",
                    self.from_screen.size[0],
                    duration=delay,
                    on_complete=self.finish_transition,
                )
            case _:
                self.container.animate(
                    "transition_offset",
                    self.from_screen.size[1],
                    duration=delay,
                    on_complete=self.finish_transition,
                )


class LiquidScreen(Screen):
    def on_screen_resume(self) -> None:
        self.focus()

    def on_show(self, *args, **kwargs):
        self.app.screen_showed()
        if 0:
            self.app.log(f"{self} - on_Show")
            width, height = self.size
            console = Console(
                width=width,
                height=height,
                file=io.StringIO(),
                force_terminal=True,
                color_system="truecolor",
                record=True,
                legacy_windows=False,
            )
            screen_render = self.app.screen._compositor.render(full=True)
            console.print(screen_render)
            text = console.export_text(styles=True)

            self.app.log(f"text from screen: {len(text)=}")
