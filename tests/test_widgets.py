"""Behavioural tests for individual widgets."""

from datetime import UTC, datetime

from conftest import run_pilot
from textual.widgets import Button, Label, Static

from termdash.app import Termdash
from termdash.config import parse_config
from termdash.services import WeatherError, WeatherReading
from termdash.services import weather as weather_service
from termdash.widgets.clock import Clock
from termdash.widgets.stopwatch import Stopwatch, StopwatchDisplay
from termdash.widgets.sysmon import HistoryGraph, SysMon
from termdash.widgets.timer import Timer, TimerDisplay


def config_for(body: str):
    return parse_config(body, source="test")


def test_clock_shows_fixed_time(monkeypatch):
    fixed = datetime(2026, 9, 27, 12, 34, 56, tzinfo=UTC)
    monkeypatch.setattr(Clock, "now", lambda self: fixed)
    config = config_for(
        '[widgets]\nkind = "clock"\nopts = { timezone = "UTC", label = "HQ" }\n'
    )

    async def scenario(pilot):
        clock = pilot.app.query_one(Clock)
        assert clock.time_text == "12:34:56"
        assert "UTC" in str(clock.query_one("#clock-zone", Label).render())
        assert "HQ" in str(clock.query_one(".caption", Label).render())

    run_pilot(Termdash(config), scenario)


def test_timer_accepts_digit_input(monkeypatch):
    config = config_for('[widgets]\nkind = "timer"\n')

    async def scenario(pilot):
        display = pilot.app.query_one(TimerDisplay)
        await pilot.click("TimerDisplay")
        await pilot.press("1", "3", "0", "enter")
        assert display.time_text == "00:01:30"
        assert pilot.app.query_one(Timer).mode == "stopped"

    run_pilot(Termdash(config), scenario)


def test_timer_caption_fits_inside_tight_tile():
    config = config_for('[widgets]\nkind = "timer"\n')

    async def scenario(pilot):
        timer = pilot.app.query_one(Timer)
        caption = timer.query_one(".caption", Label)
        content_bottom = timer.region.y + timer.region.height - 2
        assert caption.region.y + caption.region.height <= content_bottom

    run_pilot(Termdash(config), scenario, size=(40, 16))


def test_timer_editing_is_rejected_while_running():
    config = config_for('[widgets]\nkind = "timer"\nopts = { preset_seconds = 300 }\n')

    async def scenario(pilot):
        display = pilot.app.query_one(TimerDisplay)
        await pilot.click("#timer-control")
        await pilot.pause(0.15)
        assert pilot.app.query_one(Timer).mode == "running"

        await pilot.click("TimerDisplay")
        await pilot.pause(0.15)
        assert not display.editing

    run_pilot(Termdash(config), scenario)


def test_timer_completion_cycle():
    config = config_for('[widgets]\nkind = "timer"\nopts = { preset_seconds = 1 }\n')

    async def scenario(pilot):
        timer = pilot.app.query_one(Timer)
        await pilot.click("#timer-control")
        await pilot.pause(0.2)
        assert timer.mode == "running"

        await pilot.pause(1.4)
        assert timer.mode == "complete"
        assert "complete" in timer.classes

        await pilot.click("#timer-control")
        await pilot.pause(0.15)
        assert timer.mode == "stopped"
        assert "complete" not in timer.classes
        assert pilot.app.query_one(TimerDisplay).time_text == "00:00:01"

    run_pilot(Termdash(config), scenario)


def test_stopwatch_time_advances_while_running():
    config = config_for('[widgets]\nkind = "stopwatch"\n')

    async def scenario(pilot):
        display = pilot.app.query_one(StopwatchDisplay)
        await pilot.click("#start")
        await pilot.pause(0.3)
        await pilot.click("#stop")
        await pilot.pause(0.1)
        assert display.time_text != "00:00:00.00"
        assert display.total >= 0.3

    run_pilot(Termdash(config), scenario)


def test_timer_rejects_invalid_digit_input(monkeypatch):
    config = config_for('[widgets]\nkind = "timer"\n')

    async def scenario(pilot):
        await pilot.click("TimerDisplay")
        await pilot.press("1", "2", "6", "0", "6", "0", "enter")
        timer = pilot.app.query_one(Timer)
        assert timer.mode == "stopped"

    run_pilot(Termdash(config), scenario)


def test_timer_start_and_stop():
    config = config_for('[widgets]\nkind = "timer"\nopts = { preset_seconds = 300 }\n')

    async def scenario(pilot):
        timer = pilot.app.query_one(Timer)
        assert timer.mode == "stopped"
        assert pilot.app.query_one(TimerDisplay).time_text == "00:05:00"
        await pilot.click("#timer-control")
        await pilot.pause(0.15)
        assert timer.mode == "running"
        await pilot.click("#timer-control")
        await pilot.pause(0.15)
        assert timer.mode == "stopped"

    run_pilot(Termdash(config), scenario)


def test_stopwatch_controls():
    config = config_for('[widgets]\nkind = "stopwatch"\n')

    async def scenario(pilot):
        stopwatch = pilot.app.query_one(Stopwatch)
        display = pilot.app.query_one(StopwatchDisplay)
        assert display.time_text == "00:00:00.00"
        await pilot.click("#start")
        assert "started" in stopwatch.classes
        assert pilot.app.query_one("#reset", Button).disabled
        await pilot.click("#stop")
        assert "started" not in stopwatch.classes
        assert not pilot.app.query_one("#reset", Button).disabled
        await pilot.click("#reset")
        assert display.time_text == "00:00:00.00"

    run_pilot(Termdash(config), scenario)


def test_sysmon_shows_cpu_and_memory(monkeypatch):
    monkeypatch.setattr(SysMon, "cpu_percent", lambda self: 42.0)
    monkeypatch.setattr(SysMon, "mem_percent", lambda self: 77.0)
    config = config_for('[widgets]\nkind = "sysmon"\n')

    async def scenario(pilot):
        assert "CPU 42%" in str(pilot.app.query_one("#cpu-label", Label).render())
        assert "MEM 77%" in str(pilot.app.query_one("#mem-label", Label).render())
        graph = pilot.app.query_one("#cpu-graph", HistoryGraph)
        assert graph.samples == [42.0]
        assert "▄" in str(graph.render())

    run_pilot(Termdash(config), scenario)


def test_weather_shows_reading(monkeypatch):
    async def fake(location, units, *, timeout=8.0):
        return WeatherReading(
            location="Melbourne, Australia",
            temperature=21.0,
            apparent_temperature=20.0,
            wind_speed=11.0,
            weather_code=2,
            units=units,
        )

    monkeypatch.setattr(weather_service, "get_current_weather", fake)
    config = config_for(
        '[widgets]\nkind = "weather"\nopts = { location = "Melbourne" }\n'
    )

    async def scenario(pilot):
        await pilot.pause(0.3)
        current = str(pilot.app.query_one("#weather-current", Static).render())
        location = str(pilot.app.query_one("#weather-location", Label).render())
        assert "21°C" in current
        assert "Partly cloudy" in current
        assert location == "Melbourne, Australia"

    run_pilot(Termdash(config), scenario)


def test_weather_shows_error(monkeypatch):
    async def fake(location, units, *, timeout=8.0):
        raise WeatherError("network down")

    monkeypatch.setattr(weather_service, "get_current_weather", fake)
    config = config_for('[widgets]\nkind = "weather"\n')

    async def scenario(pilot):
        await pilot.pause(0.3)
        current = str(pilot.app.query_one("#weather-current", Static).render())
        error = str(pilot.app.query_one("#weather-error", Static).render())
        assert "Weather unavailable" in current
        assert "network down" in error

    run_pilot(Termdash(config), scenario)
