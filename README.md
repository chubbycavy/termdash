# termdash

[![CI](https://github.com/chubbycavy/termdash/actions/workflows/ci.yml/badge.svg)](https://github.com/chubbycavy/termdash/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/termdash)](https://pypi.org/project/termdash/)

A configurable terminal dashboard built with [Textual](https://textual.textualize.io/).
Arrange clocks, timers, system monitors, and weather into nested tiles with
**weighted layouts**, **typed options**, and **themes**.

## Requirements

- Python 3.12 or newer
- A terminal with Unicode glyph and mouse support
- Internet access for the Weather widget

## Installation

Install [uv](https://docs.astral.sh/uv/), then:

```powershell
uv tool install termdash
termdash
```

From a source checkout:

```powershell
uv sync
uv run termdash
```

## Configuration

termdash loads `~/.config/termdash/termdash.toml` when it exists (on Windows:
`%LOCALAPPDATA%\termdash\termdash.toml`; on macOS: `~/Library/Preferences/
termdash/termdash.toml`). Otherwise it uses the packaged default in
`defaults/termdash.toml`. Override the lookup with `--config PATH` or the
`TERMDASH_CONFIG` environment variable.

The layout is a tree of widget tables. Every widget table needs a `kind`.
`hbox` splits its space left-to-right and `vbox` splits top-to-bottom; every
other `kind` is a leaf tile. Any node can carry `weight` (default `1`) to claim
a proportionally larger share of its parent:

```toml
theme = "nord"

[widgets]
kind = "hbox"

[widgets.left]
kind = "vbox"

[widgets.left.clock]
kind = "clock"
opts = { timezone = "Australia/Sydney" }

[widgets.right]
kind = "vbox"
weight = 2

[widgets.right.weather]
kind = "weather"
opts = { location = "Melbourne", units = "metric", refresh_minutes = 15 }
```

Widget options go in `opts` and are validated against each widget's schema.
Unknown widgets and invalid options render as a warning tile in place, and
`termdash validate` reports every problem with its full path.

## Built-in widgets

| kind | options |
| --- | --- |
| `clock` | `timezone` (`local`, `UTC`, `UTC+9`, or IANA name), `label` |
| `timer` | `preset_seconds` (initial countdown) |
| `stopwatch` | — |
| `sysmon` | `interval` (seconds between samples), `history` (graph samples) |
| `weather` | `location`, `units` (`metric`/`imperial`), `refresh_minutes` |
| `todo` | `max_items` (summary cap), `database` (path override) |
| `spacer` | — (empty tile) |
| `hbox` / `vbox` | layout containers; child tables are their children |

Run `termdash list-widgets` for the live option list.

### Todos

The `todo` widget stores todos in a local SQLite database — on Windows
`%LOCALAPPDATA%\termdash\todo.db`, on Linux `~/.local/state/termdash/todo.db`,
on macOS `~/Library/Application Support/termdash/todo.db` (override with
`opts.database`). The database is created automatically on your first save.

Select **Manage todos** to enter the menu; menus support the arrow keys and
these Vim-inspired bindings:

- `j` / `k`: move down / up
- `g` / `G`: move to the first / last option
- `l` or `Enter`: select
- `Esc`: go back

Deleting a todo or clearing the whole database asks for confirmation first.

## Themes

`theme = "dark" | "light" | "nord" | "gruvbox" | "solarized"` at the top of the
config.

## CLI

```powershell
termdash                       # run the dashboard (Ctrl+Q to quit)
termdash validate              # check the config and report all problems
termdash list-widgets          # show every widget and its options
termdash screenshot -o out.svg # render one frame to SVG (great for previews)
```

## Development

```powershell
uv sync
uv run ruff check .
uv run pytest
```
