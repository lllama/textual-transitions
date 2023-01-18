from dataclasses import dataclass

from rich.text import Text
from textual import log
from textual.screen import Screen
from textual.widget import Widget
from textual.widgets import Label
from textual.widgets import Static
from textual.app import ComposeResult
from textual.reactive import reactive
from textual import events


@dataclass
class ScreenInfo:
    size: tuple[int, int]
    content: str
    screen: Screen


class Floaty(Label):
    CSS = """
    Floaty {
        dock: top;
        margin: 0 0;
        layer: slider;
    }
    """
    offset_x = reactive(0)
    offset_y = reactive(0)

    def __init__(self, original: Widget, *args, **kwargs):
        self.original = original
        super().__init__(*args, **kwargs)
        self.styles.margin = (original.region.y, 0, 0, original.region.x)
        self.offset_x = original.region.x
        self.offset_y = original.region.y

    def watch_offset_x(self, new_value):
        margin = self.styles.margin
        self.styles.margin = (margin.top, margin.right, margin.bottom, round(new_value))

    def watch_offset_y(self, new_value):
        margin = self.styles.margin
        self.styles.margin = (
            round(new_value),
            margin.right,
            margin.bottom,
            margin.left,
        )

    def on_show(self):
        self.parent.float_this()


class TransitionContainer(Widget):
    DEFAULT_CSS = """
    Screen TransitionContainer {
        height: 100%;
        width: 100%;
        layers: normal slider;
        layout: vertical;
        overflow: hidden;
    }
    """
    transition_offset = reactive(0.0)

    def __init__(self, from_screen, to_screen, transition):
        self.transition = transition
        self.from_screen_info: ScreenInfo = from_screen
        self.fade_out = True
        self.to_screen_info: ScreenInfo = to_screen
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
            case "slideover_left":
                from_columns = [
                    x[0 : self.width - round(self.transition_offset)]
                    for x in self.from_screen.split()
                ]
                to_columns = [
                    x[0 : round(self.transition_offset)] for x in self.to_screen.split()
                ]

                for (from_line, to_line) in zip(from_columns, to_columns):
                    yield Text("").join([from_line, to_line])
            case "wipe_left":
                from_columns = [
                    x[0 : self.width - round(self.transition_offset)]
                    for x in self.from_screen.split()
                ]
                to_columns = [
                    x[self.width - round(self.transition_offset) : self.width - 1]
                    for x in self.to_screen.split()
                ]

                for (from_line, to_line) in zip(from_columns, to_columns):
                    yield Text("").join([from_line, to_line])
            case "slide_right":
                from_offset = max(0, self.width - round(self.transition_offset) - 1)

                from_columns = [x[0:from_offset] for x in self.from_screen.split()]
                to_columns = [
                    x[from_offset : self.width] for x in self.to_screen.split()
                ]

                for lines in zip(to_columns, from_columns):
                    yield Text("").join(lines)
            case "slideover_right":
                from_offset = max(0, self.width - round(self.transition_offset) - 1)

                from_columns = [
                    x[round(self.transition_offset) : self.width - 1]
                    for x in self.from_screen.split()
                ]
                to_columns = [
                    x[from_offset : self.width] for x in self.to_screen.split()
                ]

                for lines in zip(to_columns, from_columns):
                    yield Text("").join(lines)
            case "wipe_right":
                from_offset = max(0, self.width - round(self.transition_offset) - 1)

                from_columns = [
                    x[round(self.transition_offset) : self.width - 1]
                    for x in self.from_screen.split()
                ]
                to_columns = [
                    x[0 : round(self.transition_offset)] for x in self.to_screen.split()
                ]

                for lines in zip(to_columns, from_columns):
                    yield Text("").join(lines)
            case "fade_up" | "fade_down" | "fade_left" | "fade_right" | "morph":
                log(self.transition_offset, self.fade_out)
                if self.fade_out:
                    self.styles.opacity = f"{round(105-self.transition_offset*2)+1}%"
                    if self.transition_offset >= 50:
                        self.fade_out = False
                        log(self.transition_offset, self.fade_out)
                    yield self.from_screen
                else:
                    self.styles.opacity = f"{round(self.transition_offset*2-100)}%"
                    # self.styles.opacity = "25%"
                    yield self.to_screen

    def morph(self):
        from_ids = set(
            x.id for x in self.from_screen_info.screen.walk_children() if x.id
        )
        to_ids = set(x.id for x in self.to_screen_info.screen.walk_children() if x.id)
        morph_id = from_ids.intersection(to_ids)
        if len(morph_id) > 1 or not morph_id:
            raise Exception()
        morph_id = morph_id.pop()

        self.from_widget = self.from_screen_info.screen.query_one(f"#{morph_id}")
        self.to_widget = self.to_screen_info.screen.query_one(f"#{morph_id}")
        self.floaty = Floaty(self.from_widget, self.from_widget.renderable)
        self.floaty.styles.layer = "slider"
        self.floaty.styles.border = self.from_widget.styles.border
        self.floaty.styles.width = self.from_widget.region.width
        self.screen.mount(self.floaty)

    def float_this(self):
        duration = 0.75
        self.animate(
            "transition_offset",
            100,
            duration=1.5,
            on_complete=self.screen.app.pop_screen,
        )
        self.floaty.animate("offset_x", self.to_widget.region.x, duration=duration)
        self.floaty.animate("offset_y", self.to_widget.region.y, duration=duration)
        self.floaty.styles.animate(
            "width",
            self.to_widget.region.width,
            duration=duration,
        )

    def render(self):
        return self


class TransitionScreen(Screen):

    CSS = """
    TransitionScreen {
        layout: vertical;
        layers: normal slider;
        padding: 0;
        margin: 0;
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

    def float_this(self):
        self.container.float_this()

    def finish_transition(self):
        self.app.pop_screen()

    def on_show(self, event) -> None:
        delay = 2
        self.app.log(self.transition)
        match self.transition:
            case "slide_up" | "slide_down" | "slideover_up" | "slideover_down" | "wipe_up" | "wipe_down":
                self.container.animate(
                    "transition_offset",
                    self.from_screen.size[1],
                    duration=delay,
                    on_complete=self.finish_transition,
                )
            case "slide_left" | "slide_right" | "slideover_left" | "slideover_right" | "wipe_left" | "wipe_right":
                self.container.animate(
                    "transition_offset",
                    self.from_screen.size[0],
                    duration=delay,
                    on_complete=self.finish_transition,
                )
            case "fade_up" | "fade_down" | "fade_left" | "fade_right":
                self.container.animate(
                    "transition_offset",
                    100,
                    duration=delay,
                    on_complete=self.finish_transition,
                )
            case "morph":
                self.container.morph()
            case _:
                self.container.animate(
                    "transition_offset",
                    self.from_screen.size[1],
                    duration=delay,
                    on_complete=self.finish_transition,
                )


class MessageScreen(Screen):
    direction = "up"

    def compose(self):
        yield Static("hello")


class LiquidScreen(Screen):
    def on_screen_resume(self):
        self.need_transition = True

    def on_show(self, event):
        self.app.screen_showed()
        self.need_transition = False

    def _refresh_layout(self, size=None, full: bool = False) -> None:
        """Refresh the layout (can change size and positions of widgets)."""
        size = self.outer_size if size is None else size
        if not size:
            return

        self._compositor.update_widgets(self._dirty_widgets)
        self.update_timer.pause()
        try:
            hidden, shown, resized = self._compositor.reflow(self, size)
            Hide = events.Hide
            Show = events.Show

            for widget in hidden:
                widget.post_message_no_wait(Hide(self))

            # We want to send a resize event to widgets that were just added or change since last layout
            send_resize = shown | resized
            ResizeEvent = events.Resize

            layers = self._compositor.layers
            for widget, (
                region,
                _order,
                _clip,
                virtual_size,
                container_size,
                _,
            ) in layers:
                widget._size_updated(region.size, virtual_size, container_size)
                if widget in send_resize:
                    widget.post_message_no_wait(
                        ResizeEvent(self, region.size, virtual_size, container_size)
                    )

            for widget in shown:
                widget.post_message_no_wait(Show(self))

        except Exception as error:
            self.app._handle_exception(error)
            return
        display_update = self._compositor.render(full=True)
        if not self.need_transition:
            self.app._display(self, display_update)
        if not self.app._dom_ready:
            self.app.post_message_no_wait(events.Ready(self))
            self.app._dom_ready = True
