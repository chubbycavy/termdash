"""Runtime configuration tree produced by the TOML loader."""

from __future__ import annotations

from dataclasses import dataclass, field

from pydantic import BaseModel

INVALID_KIND = "__invalid__"


@dataclass
class WidgetNode:
    """One node of the dashboard layout tree."""

    kind: str
    weight: float = 1.0
    options: BaseModel | None = None
    message: str | None = None
    children: list[WidgetNode] = field(default_factory=list)

    @property
    def valid(self) -> bool:
        return self.message is None

    @classmethod
    def invalid(cls, message: str) -> WidgetNode:
        return cls(kind=INVALID_KIND, message=message)


@dataclass
class ParsedConfig:
    """A fully loaded configuration with every problem recorded."""

    theme: str
    root: WidgetNode
    issues: list[str] = field(default_factory=list)
    source: str = "packaged default"
