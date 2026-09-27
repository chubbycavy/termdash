"""Empty tile that simply takes its share of the layout."""

from __future__ import annotations

from textual.widgets import Static

from termdash.widgets.registry import register


@register("spacer")
class Spacer(Static):
    """An empty tile for deliberate breathing room in a layout."""

    def __init__(self) -> None:
        super().__init__("")
