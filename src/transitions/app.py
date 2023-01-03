import codecs
import asyncio
import io
import types
from itertools import cycle, zip_longest
from time import monotonic
from random import choice

from .widgets.screen import LiquidScreen, ScreenInfo, TransitionScreen

from rich.console import Console
from textual.app import App, ComposeResult
from textual.containers import Container
from textual.color import Color
from textual import log
from textual.widgets import Static, Button, Header, Footer, Placeholder
from textual.reactive import reactive
from textual.events import Event
from textual.app import App, ComposeResult
from textual.messages import Prompt
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

SCREEN_IDS = list(range(10))


class DirectionScreen(LiquidScreen):
    def __init__(self, direction):
        self.direction = direction
        super().__init__()

    def on_mount(self, event):
        self.styles.background = next(PALLETTE)

    def compose(self) -> ComposeResult:
        self.app.log(f"@@@@@@@@{self.ACTION}")
        yield from [
            Static(),
            Button(f"{self.ACTION} Up", id="up"),
            Static(),
            Button(f"{self.ACTION} Left", id="left"),
            Static(),
            Button(f"{self.ACTION} Right", id="right"),
            Static(),
            Button(f"{self.ACTION} Down", id="down"),
            Static(),
        ]

    def on_button_pressed(self, event: Button.Pressed) -> None:
        event.stop()
        self.app.log(f"button pressed in {self}")
        match self.ACTION:
            case "Slide":
                self.app.switch_screen(WipeScreen(event.button.id))
            case "Wipe":
                self.app.switch_screen(SlideOverScreen(event.button.id))
            case "SlideOver":
                self.app.switch_screen(SlideScreen(event.button.id))


class WipeScreen(DirectionScreen):
    ACTION = "Wipe"


class SlideScreen(DirectionScreen):
    ACTION = "Slide"


class SlideOverScreen(DirectionScreen):
    ACTION = "SlideOver"


class TransitionsApp(App):
    CSS_PATH = "transitions.css"

    TRANSITIONS = {
        ("slide", "wipe"): "wipe_up",
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def on_ready(self, event):
        self.screen.styles.background = next(PALLETTE)

    def on_mount(self, event):
        self.push_screen(SlideScreen("up"))

    def handle_transitions(self, screen: Screen):
        from_screen = self.screen
        to_screen = screen
        self.from_screen_info = None
        self.transition = None
        if not isinstance(screen, TransitionScreen):
            keys = []
            if isinstance(screen, str):
                keys = ((from_screen.id, to_screen), (type(from_screen), to_screen))
            elif issubclass(type(screen), Screen):
                keys = (
                    (from_screen.id, to_screen.id),
                    (type(from_screen), to_screen.id),
                    (from_screen.id, type(to_screen)),
                    (type(from_screen), type(to_screen)),
                )
            for key in keys:
                if key in self.TRANSITIONS:
                    self.transition = self.TRANSITIONS[key]
                    break

            if self.transition:
                self.log(f"found a transition: {self.transition=} {key=}")
                self.from_screen_info = self.save_screen()
            else:
                self.log(f"transition not found")

            ### Faking it for the demo
            if not self.screen.id == "_default":
                self.log("faking transaction for demo")
                self.log(to_screen.direction)
                self.from_screen_info = self.save_screen()
                transition_type = (
                    type(self.screen).__name__.replace("Screen", "").lower()
                )
                self.transition = f"{transition_type}_{to_screen.direction}"
                self.log(self.transition)

            ### Faking it for the demo
        self.log(f"pushing screen {from_screen=} --> {to_screen=}")

    def push_screen(self, screen: Screen):
        self.handle_transitions(screen)
        super().push_screen(screen)
        self.log(f"pushed screen {self.screen=}")

    def switch_screen(self, screen: Screen):
        self.handle_transitions(screen)
        super().switch_screen(screen)
        self.log(f"switched  screen {self.screen=}")

    def screen_showed(self):
        self.log(f"screen showed {self.screen=}")
        self.log(f"screens {self.screen_stack=}")
        if self.transition:
            to_screen_info = self.save_screen()
            self.push_screen(
                TransitionScreen(
                    transition=self.transition,
                    from_screen=self.from_screen_info,
                    to_screen=to_screen_info,
                )
            )
        else:
            self.from_screen_info = None

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
        self.log(f"Length from app: {self.screen=}: {len(text)=}")
        return ScreenInfo(size=self.size, content=text)


if __name__ == "__main__":
    app = TransitionsApp()
    app.run()
