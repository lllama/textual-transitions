import io
from time import monotonic
from random import choice
from pathlib import Path

from .widgets.screen import ScreenInfo, TransitionScreen

from rich.console import Console
from textual.app import App, ComposeResult
from textual import log
from textual.app import App, ComposeResult
from textual.screen import Screen


class TransitionsApp(App):
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

        self.log(f"pushing screen {from_screen=} --> {to_screen=}")

    def push_screen(self, screen: Screen):
        self.handle_transitions(screen)
        super().push_screen(screen)
        self.log(f"pushed screen {self.screen=}")

    def switch_screen(self, screen: Screen):
        self.handle_transitions(screen)
        super().switch_screen(screen)
        self.log(f"switched screen {self.screen=}")

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
        return ScreenInfo(size=self.size, content=text, screen=self.screen)
