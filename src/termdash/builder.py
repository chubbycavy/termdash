"""Compose a Textual widget tree from a validated configuration tree."""

from __future__ import annotations

from typing import Any, cast

from textual.widget import Widget

from termdash.config.schema import WidgetNode
from termdash.widgets import lookup
from termdash.widgets.invalid import InvalidWidget


def build_tree(node: WidgetNode) -> Widget | None:
    """Build the widget for a config node; invalid nodes become warning tiles."""
    return _build(node, axis=None)


def _build(node: WidgetNode, *, axis: str | None) -> Widget:
    if not node.valid:
        widget = InvalidWidget(node.message or "Invalid widget configuration")
    else:
        entry = lookup(node.kind)
        if entry is None:
            widget = InvalidWidget(f"unknown widget '{node.kind}'")
        elif entry.container:
            child_axis = "h" if entry.kind.casefold() == "hbox" else "v"
            children = [_build(child, axis=child_axis) for child in node.children]
            factory = cast(Any, entry.widget_cls)
            widget = factory(elements=children)
        else:
            widget = entry.widget_cls()
            if node.options is not None:
                for name, value in node.options.model_dump().items():
                    setattr(widget, name, value)

    if axis == "h":
        widget.styles.width = f"{node.weight}fr"
        widget.styles.height = "1fr"
    elif axis == "v":
        widget.styles.height = f"{node.weight}fr"
        widget.styles.width = "1fr"
    else:
        widget.styles.width = "1fr"
        widget.styles.height = "1fr"
    return widget
