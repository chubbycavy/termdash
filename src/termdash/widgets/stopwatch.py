"""Stopwatch tile."""

from __future__ import annotations

from time import monotonic

from textual.app import ComposeResult
from textual.containers import HorizontalGroup, VerticalGroup
from textual.reactive import reactive
from textual.widgets import Button, Digits, Label

from termdash.widgets.common import TILE_CSS
from termdash.widgets.registry import register


class StopwatchDisplay(Digits):
    """Elapsed-time display ticking at 60 Hz while running."""

    total = reactive(0.0)
    elapsed = reactive(0.0)
    start_time = 0.0
    time_text = ""

    def on_mount(self) -> None:
        self.ticker = self.set_interval(1 / 60, self.tick, pause=True)
        self.render_elapsed()

    def start(self) -> None:
        self.start_time = monotonic()
        self.ticker.resume()

    def stop(self) -> None:
        self.ticker.pause()
        self.total += monotonic() - self.start_time
        self.elapsed = self.total

    def reset(self) -> None:
        self.ticker.pause()
        self.total = 0.0
        self.elapsed = 0.0

    def tick(self) -> None:
        self.elapsed = self.total + (monotonic() - self.start_time)

    def watch_elapsed(self) -> None:
        self.render_elapsed()

    def render_elapsed(self) -> None:
        minutes, seconds = divmod(self.elapsed, 60)
        hours, minutes = divmod(minutes, 60)
        self.time_text = f"{hours:02.0f}:{minutes:02.0f}:{seconds:05.2f}"
        self.update(self.time_text)


@register("stopwatch")
class Stopwatch(VerticalGroup):
    """A stopwatch with Start, Stop, and Reset controls."""

    DEFAULT_CSS = f"""
    Stopwatch {{
        {TILE_CSS}
        align: center middle;
    }}

    Stopwatch StopwatchDisplay {{
        width: 100%;
        height: 3;
        text-align: center;
    }}

    Stopwatch .controls {{
        width: 100%;
        height: 3;
        align: center middle;
    }}

    Stopwatch .controls Button {{
        width: 1fr;
    }}

    Stopwatch .caption {{
        width: 100%;
        height: 1;
        text-align: center;
        color: $text-muted;
        text-style: bold;
    }}

    Stopwatch #stop {{
        display: none;
    }}

    Stopwatch.started #start {{
        display: none;
    }}

    Stopwatch.started #stop {{
        display: block;
    }}
    """

    def compose(self) -> ComposeResult:
        yield StopwatchDisplay(id="stopwatch-display")
        with HorizontalGroup(classes="controls"):
            yield Button("Start", id="start", variant="success")
            yield Button("Stop", id="stop", variant="error")
            yield Button("Reset", id="reset")
        yield Label("Stopwatch", classes="caption", markup=False)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        display = self.query_one(StopwatchDisplay)
        reset_button = self.query_one("#reset", Button)
        if event.button.id == "start":
            display.start()
            reset_button.disabled = True
            self.add_class("started")
        elif event.button.id == "stop":
            display.stop()
            reset_button.disabled = False
            self.remove_class("started")
        elif event.button.id == "reset":
            display.reset()
