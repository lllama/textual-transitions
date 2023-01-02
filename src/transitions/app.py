import codecs
import asyncio
import io
import types
from itertools import cycle, zip_longest
from time import monotonic
from random import choice

from .widgets.matrix import Rain
from .widgets.stopwatch import Stopwatch
from .widgets.decoders import Decoder, RandomDecoder
from .widgets.progress import HackerProgress
from .widgets.xxd import XXD
from .widgets.screen import LiquidScreen, ScreenInfo

from rich.console import Console
from textual.app import App, ComposeResult
from textual.containers import Container
from textual.color import Color
from textual import log
from textual.widgets import Static, Button, Header, Footer, Placeholder
from textual.reactive import reactive
from textual.events import Event
from textual.app import App, ComposeResult
from textual.containers import Grid
from textual.screen import Screen
from textual.widgets import Static, Header, Footer, Button


PALLETTE = cycle(
    [
        "#73464c",
        "#ab5675",
        "#ee6a7c",
        "#ffa7a5",
        "#ffe07e",
        "#ffe7d6",
        "#72dcbb",
        "#34acba",
    ]
)


class DirectionScreen(LiquidScreen):
    def on_mount(self, event):
        self.styles.background = next(PALLETTE)

    def compose(self) -> ComposeResult:
        yield from [
            Static(),
            Button("Slide Up", id="up"),
            Static(),
            Button("Slide Left", id="left"),
            Static(),
            Button("Slide Right", id="right"),
            Static(),
            Button("Slide Down", id="down"),
            Static(),
        ]

    def on_button_pressed(self, event: Button.Pressed) -> None:

        self.save_screen()
        self.app.log(event.button.id)
        match event.button.id:
            case "up":
                self.app.push_screen(UpScreen())
            case "down":
                self.app.push_screen(DownScreen())
            case "left":
                self.app.push_screen(LeftScreen())
            case "right":
                self.app.push_screen(RightScreen())

    def save_screen(self) -> None:
        self.app.log("saving screen")
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
        screen_render = self.screen._compositor.render(full=True)
        console.print(screen_render)
        text = console.export_text(styles=True)
        self.app.log(len(text))

        # if not hasattr(self.app, "screen_transitions"):
        #     self.app.screen_transitions = [ScreenInfo(size=self.size, content=text)]
        # else:
        #     self.app.screen_transitions.append(ScreenInfo(size=self.size, content=text))
        self.app.screen_transitions = [ScreenInfo(size=self.size, content=text)]
        self.app.log(len(self.app.screen_transitions))


class UpScreen(DirectionScreen):
    DIRECTION = "up"


class DownScreen(DirectionScreen):
    DIRECTION = "down"


class LeftScreen(DirectionScreen):
    DIRECTION = "left"


class RightScreen(DirectionScreen):
    DIRECTION = "right"


class TransitionsApp(App):
    CSS_PATH = "transitions.css"

    def on_ready(self, event):
        self.screen.styles.background = next(PALLETTE)

    def compose(self) -> ComposeResult:
        yield from (
            Static(),
            Button("Slide Up", id="up"),
            Static(),
            Button("Slide Left", id="left"),
            Static(),
            Button("Slide Right", id="right"),
            Static(),
            Button("Slide Down", id="down"),
            Static(),
        )

    def on_button_pressed(self, event):
        self.log(event.button.id)
        self.save_screen()
        match event.button.id:
            case "up":
                self.push_screen(UpScreen())
            case "down":
                self.push_screen(DownScreen())
            case "left":
                self.push_screen(LeftScreen())
            case "right":
                self.push_screen(RightScreen())

    def push_screen(self, screen):
        self.log("pushing screen!")
        super().push_screen(screen)

    def save_screen(self) -> None:
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
        screen_render = self.screen._compositor.render(full=True)
        console.print(screen_render)
        text = console.export_text(styles=True)

        if not hasattr(self, "screen_transitions"):
            self.screen_transitions = [ScreenInfo(size=self.size, content=text)]
        else:
            self.screen_transitions.append(ScreenInfo(size=self.size, content=text))


if __name__ == "__main__":
    app = TransitionsApp()
    app.run()
