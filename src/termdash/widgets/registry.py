"""Registry mapping configuration kinds to widget classes and option schemas."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import TypeVar

from pydantic import BaseModel, ConfigDict
from textual.widget import Widget

W = TypeVar("W", bound=Widget)


class NoOptions(BaseModel):
    """Option schema for widgets that accept no options."""

    model_config = ConfigDict(extra="forbid")


@dataclass(frozen=True)
class WidgetEntry:
    """A registered widget: its config kind, class, and options schema."""

    kind: str
    widget_cls: type[Widget]
    options: type[BaseModel]
    container: bool = False


REGISTRY: dict[str, WidgetEntry] = {}


def register(
    kind: str,
    options: type[BaseModel] = NoOptions,
    *,
    container: bool = False,
) -> Callable[[type[W]], type[W]]:
    """Register a widget class under a configuration kind."""

    def decorator(cls: type[W]) -> type[W]:
        REGISTRY[kind.casefold()] = WidgetEntry(kind, cls, options, container)
        return cls

    return decorator


def lookup(kind: str) -> WidgetEntry | None:
    """Return the entry for a kind, matching case-insensitively."""
    return REGISTRY.get(kind.casefold())


def available_kinds() -> list[str]:
    """Return every registered kind, sorted."""
    return sorted(REGISTRY)
