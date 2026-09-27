"""Warning tile rendered in place of a misconfigured widget."""

from __future__ import annotations

from textual.widgets import Static


class InvalidWidget(Static):
    """A warning card that keeps the dashboard usable around a broken tile."""

    DEFAULT_CSS = """
    InvalidWidget {
        border: round $warning;
        margin: 1;
        padding: 1;
        color: $warning;
        content-align: center middle;
        text-align: center;
    }
    """

    def __init__(self, message: str) -> None:
        super().__init__(message, markup=False)
