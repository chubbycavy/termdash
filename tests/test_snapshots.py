"""SVG snapshot regression tests for the rendered dashboard."""

from conftest import freeze_environment

from termdash.app import Termdash
from termdash.config import parse_config
from termdash.storage.todo_store import TodoStore

SNAPSHOT_CONFIG = """
theme = "nord"

[widgets]
kind = "hbox"

[widgets.left]
kind = "vbox"

[widgets.left.clock]
kind = "clock"
opts = { timezone = "UTC", label = "Snapshot" }

[widgets.left.sysmon]
kind = "sysmon"
opts = { history = 10 }

[widgets.right]
kind = "vbox"
weight = 2

[widgets.right.top]
kind = "hbox"

[widgets.right.top.timer]
kind = "timer"
opts = { preset_seconds = 300 }

[widgets.right.top.stopwatch]
kind = "stopwatch"

[widgets.right.weather]
kind = "weather"
opts = { location = "Testville", units = "metric", refresh_minutes = 60 }
"""


def test_default_dashboard_snapshot(snap_compare, monkeypatch):
    freeze_environment(monkeypatch)
    app = Termdash(parse_config(SNAPSHOT_CONFIG, source="snapshot"))

    async def settle(pilot):
        await pilot.pause(0.3)

    assert snap_compare(app, terminal_size=(120, 36), run_before=settle)


def test_warning_tile_snapshot(snap_compare, monkeypatch):
    freeze_environment(monkeypatch)
    app = Termdash(
        parse_config(
            """
            theme = "gruvbox"

            [widgets]
            kind = "hbox"

            [widgets.broken]
            kind = "clock"
            opts = { timezone = "Mars/Olympus" }

            [widgets.gap]
            kind = "spacer"
            """,
            source="snapshot",
        )
    )

    async def settle(pilot):
        await pilot.pause(0.3)

    assert snap_compare(app, terminal_size=(100, 24), run_before=settle)


def todo_app(tmp_path):
    database = tmp_path / "todo.db"
    store = TodoStore(database)
    store.create_todo("Write the plan", None, "2026-10-01")
    store.create_todo("Ship termdash 0.2.0", "with todos", None)
    return Termdash(
        parse_config(
            f'[widgets]\nkind = "todo"\n'
            f'opts = {{ database = "{str(database).replace(chr(92), "/")}" }}\n',
            source="snapshot",
        )
    )


def test_todo_summary_snapshot(snap_compare, tmp_path):
    app = todo_app(tmp_path)

    async def settle(pilot):
        await pilot.pause(0.3)

    assert snap_compare(app, terminal_size=(60, 24), run_before=settle)


def test_todo_menu_snapshot(snap_compare, tmp_path):
    app = todo_app(tmp_path)

    async def open_menu(pilot):
        await pilot.pause(0.3)
        await pilot.click("#todo-manage")
        await pilot.pause(0.3)

    assert snap_compare(app, terminal_size=(60, 24), run_before=open_menu)


def test_timer_editing_snapshot(snap_compare):
    app = Termdash(
        parse_config(
            'theme = "dark"\n[widgets]\nkind = "timer"\n', source="snapshot"
        )
    )

    async def start_editing(pilot):
        await pilot.pause(0.3)
        await pilot.click("TimerDisplay")
        await pilot.pause(0.1)
        await pilot.press("1", "3", "0")

    assert snap_compare(app, terminal_size=(60, 16), run_before=start_editing)
