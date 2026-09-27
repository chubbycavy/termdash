"""Locate, read, and validate the termdash TOML configuration."""

from __future__ import annotations

import os
import tomllib
from pathlib import Path
from typing import Any

from platformdirs import user_config_dir
from pydantic import BaseModel, ValidationError

from termdash.config.schema import ParsedConfig, WidgetNode
from termdash.themes import DEFAULT_THEME, THEME_NAMES

APP_NAME = "termdash"
CONFIG_FILE_NAME = "termdash.toml"
CONFIG_ENV_VAR = "TERMDASH_CONFIG"

WIDGET_KEYS = {"kind", "weight", "opts"}
TOP_LEVEL_KEYS = {"theme", "widgets"}


def default_config_text() -> str:
    """Return the packaged default configuration document."""
    from importlib.resources import files

    resource = files(f"{APP_NAME}.defaults") / CONFIG_FILE_NAME
    return resource.read_text(encoding="utf-8")


def find_config_path(explicit: Path | None = None) -> Path | None:
    """Return the config file to load: explicit path, env var, or user config."""
    if explicit is not None:
        return explicit
    env_value = os.environ.get(CONFIG_ENV_VAR)
    if env_value:
        return Path(env_value)
    user_path = Path(user_config_dir(APP_NAME, appauthor=False)) / CONFIG_FILE_NAME
    if user_path.is_file():
        return user_path
    return None


def load_config(explicit: Path | None = None) -> ParsedConfig:
    """Load the resolved configuration, recording every problem found."""
    path = find_config_path(explicit)
    if path is None:
        return parse_config(default_config_text(), source="packaged default")
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as error:
        message = f"cannot read {path}: {error.strerror or error}"
        return ParsedConfig(
            theme=DEFAULT_THEME,
            root=WidgetNode.invalid(message),
            issues=[message],
            source=str(path),
        )
    return parse_config(text, source=str(path))


def parse_config(text: str, *, source: str = "packaged default") -> ParsedConfig:
    """Parse a TOML document into a validated layout tree."""
    issues: list[str] = []
    try:
        document = tomllib.loads(text)
    except tomllib.TOMLDecodeError as error:
        message = f"TOML parse error: {error}"
        return ParsedConfig(
            theme=DEFAULT_THEME,
            root=WidgetNode.invalid(message),
            issues=[message],
            source=source,
        )

    theme = DEFAULT_THEME
    raw_theme = document.get("theme", DEFAULT_THEME)
    if not isinstance(raw_theme, str):
        issues.append(f"theme: must be a string, got {type(raw_theme).__name__}")
    elif raw_theme.strip() not in THEME_NAMES:
        issues.append(
            f"theme: unknown theme '{raw_theme}'; "
            f"available themes: {', '.join(THEME_NAMES)}"
        )
    else:
        theme = raw_theme.strip()

    for key in document:
        if key not in TOP_LEVEL_KEYS:
            issues.append(
                f"unknown top-level key '{key}'; expected 'theme' or 'widgets'"
            )

    if "widgets" not in document:
        message = "config must define a [widgets] table with a 'kind'"
        issues.append(message)
        return ParsedConfig(
            theme=theme,
            root=WidgetNode.invalid(message),
            issues=issues,
            source=source,
        )

    root = _parse_node(document["widgets"], "widgets", issues)
    return ParsedConfig(theme=theme, root=root, issues=issues, source=source)


def _parse_node(raw: Any, path: str, issues: list[str]) -> WidgetNode:
    from termdash.widgets import available_kinds, lookup

    if not isinstance(raw, dict):
        return _fail(path, ["expected a widget table"], issues)

    problems: list[str] = []

    kind = ""
    raw_kind = raw.get("kind")
    if isinstance(raw_kind, str) and raw_kind.strip():
        kind = raw_kind.strip()
    else:
        problems.append("missing or invalid 'kind'; set kind = \"widget-name\"")

    weight = 1.0
    raw_weight = raw.get("weight")
    if raw_weight is not None:
        if (
            isinstance(raw_weight, bool)
            or not isinstance(raw_weight, (int, float))
            or raw_weight <= 0
        ):
            problems.append(f"weight must be a positive number, got {raw_weight!r}")
        else:
            weight = float(raw_weight)

    opts: dict[str, Any] = {}
    raw_opts = raw.get("opts")
    if raw_opts is not None:
        if isinstance(raw_opts, dict):
            opts = raw_opts
        else:
            problems.append(
                "opts must be a table; try opts = { key = \"value\" }"
            )

    stray = [
        key
        for key in raw
        if key not in WIDGET_KEYS and not isinstance(raw[key], dict)
    ]
    if stray:
        names = ", ".join(repr(key) for key in stray)
        problems.append(
            f"unknown key(s): {names}; widget options go in opts = {{ ... }}"
        )

    child_tables = {
        key: value
        for key, value in raw.items()
        if key not in WIDGET_KEYS and isinstance(value, dict)
    }

    entry = lookup(kind) if kind else None
    if kind and entry is None:
        problems.append(
            f"unknown widget '{kind}'; available: {', '.join(available_kinds())}"
        )
        return _fail(path, problems, issues)

    options: BaseModel | None = None
    if entry is not None and (opts or entry.options.model_fields):
        try:
            options = entry.options.model_validate(opts)
        except ValidationError as error:
            problems.append(_format_options_error(kind, entry.options, error))

    children: list[WidgetNode] = []
    if entry is not None and entry.container:
        children = [
            _parse_node(value, f"{path}.{key}", issues)
            for key, value in child_tables.items()
        ]
    elif entry is not None and child_tables:
        names = ", ".join(repr(key) for key in child_tables)
        problems.append(
            f"'{kind}' cannot contain child tables ({names}); only hbox/vbox can"
        )

    if problems:
        return _fail(path, problems, issues)

    return WidgetNode(
        kind=kind.casefold(), weight=weight, options=options, children=children
    )


def _fail(path: str, problems: list[str], issues: list[str]) -> WidgetNode:
    issues.extend(f"{path}: {part}" for part in problems)
    return WidgetNode.invalid(f"{path}: " + "; ".join(problems))


def _format_options_error(
    kind: str, model: type[BaseModel], error: ValidationError
) -> str:
    parts: list[str] = []
    for item in error.errors():
        location = item.get("loc") or ()
        name = str(location[0]) if location else "opts"
        if item.get("type") == "extra_forbidden":
            parts.append(f"unknown option '{name}'")
        else:
            message = str(item.get("msg", "is invalid"))
            message = message.removeprefix("Value error, ")
            parts.append(f"option '{name}' is invalid: {message}")
    fields = (
        ", ".join(sorted(model.model_fields)) if model.model_fields else "none"
    )
    return f"invalid options for '{kind}': {'; '.join(parts)}; valid options: {fields}"
