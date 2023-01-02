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

    def __init__(self, content1, content2, direction):
        self.direction = direction
        log("hello")
        self.content1_info = content1
        self.content2_info = content2
        self.content1 = Text.from_ansi(content1.content)
        self.content2 = Text.from_ansi(content2.content)
        self.width = self.content1_info.size[0]
        self.height = self.content1_info.size[1]
        super().__init__()

    def get_content_height(self, container, viewport, width: int) -> int:
        return self.content1_info.size[1]

    def get_content_width(self, container, viewport) -> int:
        return self.content1_info.size[0]

    # def watch_transition_offset(self, new_value):
    #     log(round(new_value))
    #     self.content = self.content[round(new_value) :]
    #     # log(len(self.content))

    def __rich_console__(self, console, options):
        lines = self.content1.split()
        lines.extend(self.content2.split())

        yield from lines[
            round(self.transition_offset) : round(self.transition_offset) + self.height
        ]

    def render(self):
        return self
        return Text.join(
            "",
            self.content[
                round(self.transition_offset) : round(self.transition_offset)
                + self.height
            ],
        )
        return "".join(
            x
            for x in self.content[
                round(self.transition_offset) : round(self.transition_offset)
                + self.height
            ]
        )


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

    def __init__(self, direction):
        self.direction = direction
        super().__init__()

    def compose(self) -> ComposeResult:
        self.screen2_content: ScreenInfo = self.app.screen_transitions.pop()
        self.screen1_content: ScreenInfo = self.app.screen_transitions.pop()
        self.app.log(self.direction)
        self.container = TransitionContainer(
            self.screen1_content, self.screen2_content, direction=self.direction
        )
        yield self.container

    def on_show(self, event) -> None:
        self.app.log("[blue bold]Ready to scroll!")
        delay = 5.0
        # self.app.log(len(self.screen1_content.content.splitlines()))
        self.app.log(self.screen1_content.size[1])
        self.container.animate(
            "transition_offset",
            self.screen1_content.size[1],
            # easing="in_sine",
            duration=delay,
            on_complete=self.app.pop_screen,
        )
        # self.container.scroll_end(animate=True, duration=delay)
        # self.set_timer(delay, self.app.pop_screen)


class LiquidScreen(Screen):
    def on_screen_suspend(self, event):
        self.app.log("[red bold]SUSPENDING QUIT!!")

    def on_screen_resume(self, event):
        self.app.log("[red bold]RESUMING!!")
        self.app.log(f"{len(self.app.screen_transitions)=}")

    def on_show(self, *args, **kwargs):
        self.app.log(f"{self} - on_Show")
        if len(self.app.screen_transitions) != 1:
            return
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

        if not hasattr(self.app, "screen_transitions"):
            self.app.screen_transitions = [ScreenInfo(size=self.size, content=text)]
        else:
            self.app.screen_transitions.append(ScreenInfo(size=self.size, content=text))

        self.app.log("exported!")
        self.app.log(len(self.app.screen_transitions))

        self.app.log(f"{len(self.app.screen_transitions)=}")
        if not len(self.app.screen_transitions) % 2:
            self.app.log("transitioning")
            self.app.push_screen(TransitionScreen(direction=self.DIRECTION))
