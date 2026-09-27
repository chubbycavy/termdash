"""Clock tile with timezone support."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from datetime import timezone as datetime_timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import BaseModel, ConfigDict, field_validator
from textual.app import ComposeResult
from textual.containers import VerticalGroup
from textual.reactive import reactive
from textual.widgets import Digits, Label

from termdash.widgets.common import TILE_CSS
from termdash.widgets.registry import register


class ClockOptions(BaseModel):
    """Options for the clock widget."""

    model_config = ConfigDict(extra="forbid")

    timezone: str = "local"
    label: str | None = None

    @field_validator("timezone")
    @classmethod
    def validate_timezone(cls, value: str) -> str:
        resolve_timezone(value)
        return value


def resolve_timezone(name: str):
    """Resolve a timezone name to a tzinfo; raise ValueError when unknown."""
    text = name.strip()
    lowered = text.lower()
    if lowered == "local":
        return None
    if lowered == "utc":
        return UTC
    if text.upper().startswith("UTC"):
        offset = text[3:]
        if not offset:
            return UTC
        try:
            hours = float(offset)
        except ValueError as error:
            raise ValueError("offset must look like 'UTC+2' or 'UTC-5.5'") from error
        try:
            return datetime_timezone(timedelta(hours=hours))
        except ValueError as error:
            raise ValueError("UTC offset must be between -24 and 24 hours") from error
    try:
        return ZoneInfo(text)
    except (ZoneInfoNotFoundError, ValueError) as error:
        raise ValueError(
            f"unknown timezone '{name}'; use 'local', 'UTC', 'UTC+2', "
            "or an IANA name like 'Europe/Berlin'"
        ) from error


@register("clock", ClockOptions)
class Clock(VerticalGroup):
    """A ticking 24-hour clock with timezone and caption."""

    timezone = reactive("local")
    label: str | None = None
    time_text = ""

    DEFAULT_CSS = f"""
    Clock {{
        {TILE_CSS}
        align: center middle;
    }}

    Clock Digits {{
        width: 100%;
        height: 3;
        text-align: center;
    }}

    Clock .zone,
    Clock .caption {{
        width: 100%;
        height: 1;
        margin: 1 0 0 0;
        text-align: center;
        color: $text-muted;
    }}

    Clock .caption {{
        text-style: bold;
    }}
    """

    def compose(self) -> ComposeResult:
        yield Digits(id="clock-time")
        yield Label("", id="clock-zone", classes="zone", markup=False)
        yield Label("", classes="caption", markup=False)

    def on_mount(self) -> None:
        self.refresh_time()
        self.set_interval(1, self.refresh_time)

    def watch_timezone(self) -> None:
        if self.is_mounted:
            self.refresh_time()

    def now(self) -> datetime:
        return datetime.now(resolve_timezone(self.timezone))

    def refresh_time(self) -> None:
        current = self.now()
        self.time_text = current.strftime("%H:%M:%S")
        self.query_one("#clock-time", Digits).update(self.time_text)
        self.query_one("#clock-zone", Label).update(self.zone_label())
        self.query_one(".caption", Label).update(self.label or "Clock")

    def zone_label(self) -> str:
        if self.timezone.strip().lower() == "local":
            local_name = datetime.now().astimezone().tzname() or "local"
            return f"Local ({local_name})"
        return self.timezone.strip()
