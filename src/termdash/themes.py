"""Curated theme presets for the dashboard."""

from __future__ import annotations

from textual.theme import Theme

THEMES: dict[str, Theme] = {
    "dark": Theme(
        name="dark",
        dark=True,
        primary="#7aa2f7",
        secondary="#9ece6a",
        accent="#bb9af7",
        foreground="#c0caf5",
        background="#1a1b26",
        surface="#24283b",
        panel="#24283b",
        success="#9ece6a",
        warning="#e0af68",
        error="#f7768e",
    ),
    "light": Theme(
        name="light",
        dark=False,
        primary="#2c5faf",
        secondary="#1a7f37",
        accent="#8250df",
        foreground="#1f2328",
        background="#f6f8fa",
        surface="#ffffff",
        panel="#eaeef2",
        success="#1a7f37",
        warning="#9a6700",
        error="#cf222e",
    ),
    "nord": Theme(
        name="nord",
        dark=True,
        primary="#88c0d0",
        secondary="#a3be8c",
        accent="#b48ead",
        foreground="#eceff4",
        background="#2e3440",
        surface="#3b4252",
        panel="#434c5e",
        success="#a3be8c",
        warning="#ebcb8b",
        error="#bf616a",
    ),
    "gruvbox": Theme(
        name="gruvbox",
        dark=True,
        primary="#83a598",
        secondary="#b8bb26",
        accent="#d3869b",
        foreground="#ebdbb2",
        background="#282828",
        surface="#3c3836",
        panel="#504945",
        success="#b8bb26",
        warning="#fabd2f",
        error="#fb4934",
    ),
    "solarized": Theme(
        name="solarized",
        dark=True,
        primary="#268bd2",
        secondary="#2aa198",
        accent="#6c71c4",
        foreground="#839496",
        background="#002b36",
        surface="#073642",
        panel="#586e75",
        success="#859900",
        warning="#b58900",
        error="#dc322f",
    ),
}

THEME_NAMES: list[str] = sorted(THEMES)

DEFAULT_THEME = "dark"
