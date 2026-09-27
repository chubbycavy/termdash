"""Countdown timer tile with an editable digit display."""

from __future__ import annotations

from math import ceil
from time import monotonic

from pydantic import BaseModel, ConfigDict, Field
from textual import events
from textual.app import ComposeResult
from textual.containers import HorizontalGroup, VerticalGroup
from textual.reactive import reactive
from textual.widgets import Button, Digits, Label

from termdash.widgets.common import TILE_CSS
from termdash.widgets.registry import register


class TimerOptions(BaseModel):
    """Options for the timer widget."""

    model_config = ConfigDict(extra="forbid")

    preset_seconds: int = Field(default=0, ge=0, le=359999)


class TimerDisplay(Digits):
    """Editable countdown: click while stopped, type HHMMSS, press Enter."""

    can_focus = True
    editing = reactive(False)
    remaining = reactive(0.0)
    duration = 0
    end_time = 0.0
    buffer = ""
    time_text = ""

    def on_mount(self) -> None:
        self.ticker = self.set_interval(1 / 30, self.tick, pause=True)
        self.render_remaining()

    def on_click(self, event: events.Click) -> None:
        timer = self.parent
        if isinstance(timer, Timer) and timer.mode == "stopped":
            timer.prepare_edit()
            self.buffer = ""
            self.editing = True
            self.time_text = "00:00:00"
            self.update(self.time_text)
            self.focus()
            event.stop()

    def on_key(self, event: events.Key) -> None:
        if not self.editing:
            return
        if event.key == "enter":
            self.commit()
            event.stop()
        elif event.key == "backspace":
            self.buffer = self.buffer[:-1]
            self.render_buffer()
            event.stop()
        elif event.character is not None and event.character.isdigit():
            self.buffer = (self.buffer + event.character)[-6:]
            self.render_buffer()
            event.stop()

    def render_buffer(self) -> None:
        digits = self.buffer[-6:].rjust(6, "0")
        self.time_text = f"{digits[:2]}:{digits[2:4]}:{digits[4:]}"
        self.update(self.time_text)

    def commit(self) -> None:
        seconds = self.parse_buffer(self.buffer)
        timer = self.parent
        if seconds is not None and isinstance(timer, Timer):
            timer.set_duration(seconds)
            return
        self.add_class("invalid")
        self.app.bell()
        self.set_timer(0.5, lambda: self.remove_class("invalid"))

    @staticmethod
    def parse_buffer(buffer: str) -> int | None:
        digits = buffer[-6:].rjust(6, "0")
        hours = int(digits[:2])
        minutes = int(digits[2:4])
        seconds = int(digits[4:])
        if minutes >= 60 or seconds >= 60:
            return None
        total = hours * 3600 + minutes * 60 + seconds
        return total if total > 0 else None

    def start(self) -> None:
        if self.remaining <= 0:
            return
        self.end_time = monotonic() + self.remaining
        self.ticker.resume()

    def stop(self) -> None:
        self.ticker.pause()
        self.remaining = max(0.0, self.end_time - monotonic())

    def reset(self) -> None:
        self.ticker.pause()
        self.remaining = float(self.duration)
        self.editing = False
        self.render_remaining()

    def tick(self) -> None:
        self.remaining = max(0.0, self.end_time - monotonic())
        if self.remaining <= 0:
            self.ticker.pause()
            timer = self.parent
            if isinstance(timer, Timer):
                timer.complete()

    def watch_remaining(self) -> None:
        if not self.editing:
            self.render_remaining()

    def render_remaining(self) -> None:
        total = ceil(self.remaining)
        hours, rest = divmod(total, 3600)
        minutes, seconds = divmod(rest, 60)
        self.time_text = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        self.update(self.time_text)


@register("timer", TimerOptions)
class Timer(VerticalGroup):
    """A countdown timer with a single Start/Stop/Reset control."""

    preset_seconds = 0
    mode = "stopped"

    DEFAULT_CSS = f"""
    Timer {{
        {TILE_CSS}
        align: center middle;
    }}

    Timer TimerDisplay {{
        width: 100%;
        height: 3;
        text-align: center;
    }}

    Timer TimerDisplay.editing {{
        background: $primary-muted;
    }}

    Timer TimerDisplay.invalid {{
        color: $error;
    }}

    Timer .hint,
    Timer .caption {{
        width: 100%;
        height: 1;
        text-align: center;
        color: $text-muted;
    }}

    Timer .caption {{
        text-style: bold;
    }}

    Timer .controls {{
        width: 100%;
        height: 3;
        align: center middle;
    }}

    Timer .controls Button {{
        width: 1fr;
    }}

    Timer.complete {{
        border: round $warning;
    }}

    Timer.complete.flash {{
        border: round $warning 30%;
    }}
    """

    def compose(self) -> ComposeResult:
        yield TimerDisplay(id="timer-display")
        yield Label(
            "Click digits, Enter to confirm",
            classes="hint",
            markup=False,
        )
        with HorizontalGroup(classes="controls"):
            yield Button("Start", id="timer-control", variant="success")
        yield Label("Timer", classes="caption", markup=False)

    def on_mount(self) -> None:
        self.flash_timer = self.set_interval(
            0.5, lambda: self.toggle_class("flash"), pause=True
        )
        self.set_duration(self.preset_seconds)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id != "timer-control":
            return
        if self.mode == "running":
            self.stop()
        elif self.mode == "complete":
            self.reset_timer()
        else:
            self.start()

    def prepare_edit(self) -> None:
        if self.mode == "complete":
            self.flash_timer.pause()
            self.remove_class("complete", "flash")
        self.mode = "stopped"
        self.set_control("Start", "success")

    def set_duration(self, seconds: int) -> None:
        display = self.query_one(TimerDisplay)
        display.duration = seconds
        display.remaining = float(seconds)
        display.editing = False
        display.render_remaining()
        self.mode = "stopped"
        self.set_control("Start", "success")

    def start(self) -> None:
        display = self.query_one(TimerDisplay)
        if display.remaining <= 0:
            return
        display.start()
        self.mode = "running"
        self.set_control("Stop", "error")

    def stop(self) -> None:
        self.query_one(TimerDisplay).stop()
        self.mode = "stopped"
        self.set_control("Start", "success")

    def complete(self) -> None:
        self.mode = "complete"
        self.add_class("complete")
        self.flash_timer.resume()
        self.set_control("Reset", "warning")

    def reset_timer(self) -> None:
        self.flash_timer.pause()
        self.remove_class("complete", "flash")
        self.query_one(TimerDisplay).reset()
        self.mode = "stopped"
        self.set_control("Start", "success")

    def set_control(self, label: str, variant: str) -> None:
        control = self.query_one("#timer-control", Button)
        control.label = label
        control.variant = variant
