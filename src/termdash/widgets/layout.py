"""Weighted split containers for the layout tree."""

from __future__ import annotations

from collections.abc import Iterable

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widget import Widget

from termdash.widgets.registry import NoOptions, register


class WeightedRow(Horizontal):
    """A row of children whose widths follow their configured weights."""

    DEFAULT_CSS = """
    WeightedRow {
        width: 1fr;
        height: 1fr;
    }
    """

    def __init__(self, elements: Iterable[Widget] = ()) -> None:
        super().__init__()
        self.elements = list(elements)

    def compose(self) -> ComposeResult:
        yield from self.elements


class WeightedColumn(Vertical):
    """A column of children whose heights follow their configured weights."""

    DEFAULT_CSS = """
    WeightedColumn {
        width: 1fr;
        height: 1fr;
    }
    """

    def __init__(self, elements: Iterable[Widget] = ()) -> None:
        super().__init__()
        self.elements = list(elements)

    def compose(self) -> ComposeResult:
        yield from self.elements


register("hbox", NoOptions, container=True)(WeightedRow)
register("vbox", NoOptions, container=True)(WeightedColumn)
