"""Composite widget that stacks enabled built-ins in a single tile."""

from __future__ import annotations

from typing import cast

from pydantic import BaseModel, ConfigDict, field_validator
from textual.app import ComposeResult
from textual.containers import VerticalGroup
from textual.widgets import Label, Static

from termdash.widgets.clock import Clock, resolve_timezone
from termdash.widgets.common import TILE_CSS
from termdash.widgets.registry import lookup, register

FIXED_ORDER = ("clock", "timer", "stopwatch", "sysmon", "todo", "weather")


class CustomOptions(BaseModel):
    """Options for the custom widget."""

    model_config = ConfigDict(extra="forbid")

    text: str | None = None
    clock: bool = False
    timer: bool = False
    stopwatch: bool = False
    sysmon: bool = False
    todo: bool = False
    weather: bool = False
    timezone: str = "local"

    @field_validator("timezone")
    @classmethod
    def validate_timezone(cls, value: str) -> str:
        resolve_timezone(value)
        return value


@register("custom", CustomOptions)
class Custom(VerticalGroup):
    """A one-layer stack of the enabled built-in widgets."""

    text: str | None = None
    clock = False
    timer = False
    stopwatch = False
    sysmon = False
    todo = False
    weather = False
    timezone = "local"

    DEFAULT_CSS = f"""
    Custom {{
        {TILE_CSS}
    }}

    Custom .custom-text {{
        width: 100%;
        height: 1;
        text-align: center;
        color: $text-muted;
        text-style: bold;
        margin: 0 0 1 0;
    }}

    Custom .custom-empty {{
        width: 100%;
        text-align: center;
        color: $text-muted;
    }}
    """

    def compose(self) -> ComposeResult:
        if self.text:
            yield Label(self.text, classes="custom-text", markup=False)
        enabled = [kind for kind in FIXED_ORDER if getattr(self, kind)]
        if not enabled:
            yield Static("No elements enabled", classes="custom-empty", markup=False)
            return
        for kind in enabled:
            yield self.build_element(kind)

    def build_element(self, kind: str):
        """Instantiate a registered widget with custom-tile styling."""
        entry = lookup(kind)
        if entry is None:
            raise ValueError(f"unknown custom element '{kind}'")
        element = entry.widget_cls()
        if kind == "clock":
            cast(Clock, element).timezone = self.timezone
        element.styles.width = "1fr"
        element.styles.height = "auto"
        return element
