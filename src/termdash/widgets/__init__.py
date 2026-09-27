"""Built-in termdash widgets; importing this package registers them all."""

from termdash.widgets import (
    clock,
    layout,
    spacer,
    stopwatch,
    sysmon,
    timer,
    todo,
    weather,
)
from termdash.widgets.registry import (
    REGISTRY,
    NoOptions,
    WidgetEntry,
    available_kinds,
    lookup,
    register,
)

__all__ = [
    "REGISTRY",
    "NoOptions",
    "WidgetEntry",
    "available_kinds",
    "clock",
    "layout",
    "lookup",
    "register",
    "spacer",
    "stopwatch",
    "sysmon",
    "timer",
    "todo",
    "weather",
]
