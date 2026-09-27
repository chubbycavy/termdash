"""The termdash Textual application."""

from __future__ import annotations

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container
from textual.widgets import Footer, Header, Static

from termdash import themes as theme_defs
from termdash.builder import build_tree
from termdash.config.schema import ParsedConfig


class Termdash(App):
    """Compose and run the configured terminal dashboard."""

    TITLE = "termdash"
    BINDINGS = [Binding("ctrl+q", "quit", "Quit", key_display="^q")]

    DEFAULT_CSS = """
    #config-warning-screen {
        width: 1fr;
        height: 1fr;
        align: center middle;
    }

    #config-warning {
        width: 60;
        height: auto;
        max-height: 18;
        border: round $warning;
        padding: 1;
        color: $warning;
        content-align: center middle;
        text-align: center;
    }
    """

    def __init__(self, config: ParsedConfig, **kwargs) -> None:
        super().__init__(**kwargs)
        self.dashboard_config = config
        for theme in theme_defs.THEMES.values():
            self.register_theme(theme)

    def on_mount(self) -> None:
        self.theme = self.dashboard_config.theme

    def compose(self) -> ComposeResult:
        yield Header(show_clock=False)
        root_config = self.dashboard_config.root
        layout = build_tree(root_config) if root_config.valid else None
        if layout is None:
            message = root_config.message or "Configuration could not be loaded."
            with Container(id="config-warning-screen"):
                yield Static(
                    f"{message}\n\n"
                    "Fix termdash.toml and restart, or run: termdash validate",
                    id="config-warning",
                    markup=False,
                )
        else:
            yield layout
        yield Footer()
