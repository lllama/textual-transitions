from itertools import cycle
from random import choice
from pathlib import Path
import io
from .app import TransitionsApp
from .widgets.screen import TransitionScreen, LiquidScreen, Floaty


from textual.events import Event
from textual.screen import Screen
from textual.widget import Widget
from textual.widgets import Label, Static, Checkbox, Button, TextLog
from textual.containers import Vertical, Horizontal
from textual.app import ComposeResult
from rich.console import Console
from rich.markdown import Markdown


from rich_pixels import Pixels

PALLETTE1 = [
    "#73464c",
    "#ab5675",
    "#ee6a7c",
    "#ffa7a5",
    "#ffe07e",
    "#ffe7d6",
    "#72dcbb",
    "#34acba",
]

PALLETTE2 = [
    "#0d2b45",
    "#203c56",
    "#544e68",
    "#8d697a",
    "#d08159",
    "#ffaa5e",
]
PALLETTE = cycle(PALLETTE2)
SCREEN_IDS = list(range(10))

PLACEHOLDER_VARIANTS = ["default", "size", "text"]

IMAGES = cycle(["will.jpeg", "darren.jpeg", "dave.jpeg"])


class DirectionScreen(LiquidScreen):
    TYPES = {"slide", "slideover", "wipe", "fade"}
    DIRECTIONS = {"up", "down", "left", "right"}

    def __init__(self, direction):
        self.direction = direction
        self.toggling = False
        super().__init__()

    def on_mount(self, event):
        self.styles.background = next(PALLETTE)
        border_style = choice(
            (
                "ascii",
                "blank",
                "dashed",
                "double",
                "heavy",
                "hidden",
                "hkey",
                "inner",
                "none",
                "outer",
                "round",
                "solid",
                "tall",
                "vkey",
                "wide",
            )
        )
        self.styles.border = (border_style, next(PALLETTE))

    def compose(self) -> ComposeResult:
        yield Vertical(
            Static("[b]Transition Types", classes="label"),
            Horizontal(
                Static("Slide:        ", classes="label"),
                Checkbox(id="slide", value=True),
                classes="container",
            ),
            Horizontal(
                Static("Slide Over:   ", classes="label"),
                Checkbox(id="slideover"),
                classes="container",
            ),
            Horizontal(
                Static("Wipe:         ", classes="label"),
                Checkbox(id="wipe"),
                classes="container",
            ),
            Horizontal(
                Static("Fade:         ", classes="label"),
                Checkbox(id="fade"),
                classes="container",
            ),
            Static("[b]Direction", classes="label directions"),
            Horizontal(
                Static("Up:           ", classes="label"),
                Checkbox(value=True, id="up"),
                classes="container",
            ),
            Horizontal(
                Static("Down:         ", classes="label"),
                Checkbox(id="down"),
                classes="container",
            ),
            Horizontal(
                Static("Left:         ", classes="label"),
                Checkbox(id="left"),
                classes="container",
            ),
            Horizontal(
                Static("Right:        ", classes="label"),
                Checkbox(id="right"),
                classes="container",
            ),
            Button("TRANSITION"),
            Button("It's Morphin' time!", id="morbin"),
            classes="container",
        )

        yield Static(Pixels.from_image_path(next(IMAGES), resize=(50, 50)))

    def done_toggling(self):
        self.toggling = False

    def on_checkbox_changed(self, event):
        event.stop()
        if event.value == False and not self.toggling:
            # Can't disable all checkboxes
            event.input.toggle()
            return
        if self.toggling:
            return
        if event.input.id in self.TYPES:
            self.toggling = True
            for checkbox in self.TYPES - {event.input.id}:
                self.query_one(f"#{checkbox}").value = False
        elif event.input.id in self.DIRECTIONS:
            self.toggling = True
            for checkbox in self.DIRECTIONS - {event.input.id}:
                self.query_one(f"#{checkbox}").value = False

        if self.toggling:
            self.set_timer(0.1, self.done_toggling)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        event.stop()

        for effect in self.TYPES:
            checkbox = self.query_one(f"#{effect}")
            if checkbox.value:
                break
        for direction in self.DIRECTIONS:
            checkbox = self.query_one(f"#{direction}")
            if checkbox.value:
                break

        transition = f"{effect}_{direction}"
        self.app.log(f"Performing transition: {transition}")
        if event.button.id == "morbin":
            self.app.switch_screen(MorphScreenOne())
        else:
            self.app.switch_screen(DirectionScreen(direction=transition))


class WipeScreen(DirectionScreen):
    ACTION = "Wipe"


class SlideScreen(DirectionScreen):
    ACTION = "Slide"


class SlideOverScreen(DirectionScreen):
    ACTION = "SlideOver"


class Title(Label):
    def on_click(self, event: Event):
        self.screen.app.push_screen(MorphScreenTwo(self))


class MorphScreenTwo(LiquidScreen):
    def __init__(self, widget, *args, **kwargs):
        self.widget = widget
        super().__init__(*args, **kwargs)

    def compose(self):
        self.heading = Label(self.widget.renderable, id=self.widget.id)
        self.heading.styles.width = "100%"
        yield self.heading
        yield Button("Back to start")
        text = (Path("docs/") / f"{self.widget.id}.md").read_text()
        self.textlog = TextLog(highlight=True, markup=True)
        self.textlog.write(text)
        yield Static(Markdown(text))

    def on_click(self):
        self.app.push_screen(MorphScreenOne())

    def on_button_pressed(self, event: Button.Pressed) -> None:
        event.stop()

        transition = "fade_up"
        self.app.log(f"Performing transition: {transition}")
        self.app.switch_screen(DirectionScreen(direction=transition))


class MorphScreenOne(LiquidScreen):
    direction = "up"

    def compose(self):
        self.heading = Label("Textual Docs", id="heading")
        yield self.heading
        for doc in Path("./docs/").glob("*.md"):
            yield Title(doc.stem, id=doc.stem)

    def mount_this(self, title: Title):
        self.app.log("floating")
        layers = list(self.styles.layers)
        if "slider" not in layers:
            layers.append("slider")
        self.styles.layers = tuple(layers)
        self.old_title = title
        self.new_title = Floaty(title, title.renderable)
        self.new_title.styles.layer = "slider"

        self.mount(self.new_title)

    def float_this(self, title):
        if hasattr(self, "new_title") and self.new_title is title:
            self.new_title.animate(
                "offset_x",
                self.heading.region.x,
                duration=1,
            )
            self.new_title.animate(
                "offset_y",
                self.heading.region.y,
                duration=1,
                on_complete=lambda: self.app.push_screen(MorphScreenTwo()),
            )
            self.new_title.styles.width = self.new_title.region.width
            self.new_title.styles.animate(
                "width",
                self.heading.region.width,
                duration=1,
            )
            for title in self.query(Widget):
                if title is self.new_title:
                    continue
                title.styles.animate("opacity", 0.05, duration=1)
            self.styles.animate("opacity", 0.10, duration=1)


class DemoApp(TransitionsApp):
    CSS_PATH = "transitions.css"
    TRANSITIONS = {}

    def on_mount(self):
        self.push_screen(DirectionScreen("up"))

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

            ### Ignore all the above
            ### Faking it for the demo
            if not self.screen.id == "_default":
                self.log("faking transaction for demo")
                self.from_screen_info = self.save_screen()

                if self.screen.__class__.__name__ in (
                    "MorphScreenOne",
                    "MorphScreenTwo",
                ) and to_screen.__class__.__name__ in (
                    "MorphScreenOne",
                    "MorphScreenTwo",
                ):
                    self.log("It's morbin time!")
                    self.transition = "morph"
                else:
                    self.log(to_screen.direction)
                    transition_type = (
                        type(self.screen).__name__.replace("Screen", "").lower()
                    )
                    self.transition = to_screen.direction
                    self.log(self.transition)

            ### Faking it for the demo
        self.log(f"pushing screen {from_screen=} --> {to_screen=}")


if __name__ == "__main__":
    DemoApp().run()
