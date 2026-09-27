"""Tests for the Custom composite widget."""

from datetime import UTC

from conftest import run_pilot
from textual.widgets import Label, Static

from termdash.app import Termdash
from termdash.config import parse_config
from termdash.widgets.clock import Clock
from termdash.widgets.custom import Custom
from termdash.widgets.timer import Timer
from termdash.widgets.weather import Weather


def custom_config(opts: str):
    return parse_config(
        f'[widgets]\nkind = "custom"\nopts = {{ {opts} }}\n', source="test"
    )


def test_children_follow_the_fixed_order(monkeypatch):
    from datetime import datetime

    monkeypatch.setattr(
        Clock, "now", lambda self: datetime(2026, 1, 1, 0, 0, 0, tzinfo=UTC)
    )
    config = custom_config(
        'weather = true, timer = true, clock = true, sysmon = true'
    )

    async def scenario(pilot):
        custom = pilot.app.query_one(Custom)
        kinds = [
            type(child).__name__
            for child in custom.children
            if not isinstance(child, (Label, Static))
        ]
        assert kinds == ["Clock", "Timer", "SysMon", "Weather"]

    run_pilot(Termdash(config), scenario)


def test_disabled_widgets_are_not_rendered():
    config = custom_config('clock = true')

    async def scenario(pilot):
        custom = pilot.app.query_one(Custom)
        assert len(pilot.app.query(Timer)) == 0
        assert len(pilot.app.query(Weather)) == 0
        assert len(pilot.app.query(Clock)) == 1
        assert len(custom.children) == 1

    run_pilot(Termdash(config), scenario)


def test_timezone_reaches_the_nested_clock(monkeypatch):
    from datetime import datetime

    monkeypatch.setattr(
        Clock, "now", lambda self: datetime(2026, 1, 1, 12, 0, 0, tzinfo=UTC)
    )
    config = custom_config('clock = true, timezone = "UTC"')

    async def scenario(pilot):
        clock = pilot.app.query_one(Clock)
        assert clock.timezone == "UTC"
        assert clock.time_text == "12:00:00"

    run_pilot(Termdash(config), scenario)


def test_text_heading_is_shown():
    config = custom_config('text = "Focus time"')

    async def scenario(pilot):
        custom = pilot.app.query_one(Custom)
        heading = custom.query_one(".custom-text", Label)
        assert str(heading.render()) == "Focus time"
        empty = custom.query_one(".custom-empty", Static)
        assert str(empty.render()) == "No elements enabled"

    run_pilot(Termdash(config), scenario)


def test_completely_empty_state_shows_placeholder():
    config = custom_config("")

    async def scenario(pilot):
        custom = pilot.app.query_one(Custom)
        empty = custom.query_one(".custom-empty", Static)
        assert str(empty.render()) == "No elements enabled"
        assert len(custom.children) == 1

    run_pilot(Termdash(config), scenario)


def test_unknown_switch_is_a_typed_error():
    config = custom_config('purple = true')
    assert not config.root.valid
    issue = config.issues[0]
    assert "unknown option 'purple'" in issue
    assert (
        "valid options: clock, stopwatch, sysmon, text, timer, timezone, todo, weather"
        in issue
    )


def test_invalid_nested_timezone_is_rejected_at_load():
    config = custom_config('clock = true, timezone = "Mars/Olympus"')
    assert not config.root.valid
    assert "unknown timezone 'Mars/Olympus'" in config.issues[0]
