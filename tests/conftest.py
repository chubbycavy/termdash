"""Shared helpers for termdash tests."""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime

from textual.app import App
from textual.pilot import Pilot


def run_pilot(
    app: App,
    scenario: Callable[[Pilot], Awaitable[None]],
    size: tuple[int, int] = (100, 30),
) -> None:
    """Run an app headlessly and execute an async scenario against its pilot."""

    async def wrapper() -> None:
        async with app.run_test(size=size) as pilot:
            await pilot.pause()
            await scenario(pilot)

    asyncio.run(wrapper())


def freeze_environment(monkeypatch) -> None:
    """Pin clock, sysmon, and weather outputs for deterministic renderings."""

    from termdash.services import weather as weather_service
    from termdash.widgets.clock import Clock
    from termdash.widgets.sysmon import SysMon

    fixed = datetime(2026, 1, 1, 12, 0, 0, tzinfo=UTC)
    monkeypatch.setattr(Clock, "now", lambda self: fixed)
    monkeypatch.setattr(SysMon, "cpu_percent", lambda self: 42.0)
    monkeypatch.setattr(SysMon, "mem_percent", lambda self: 77.0)

    async def fake_weather(location, units, *, timeout=8.0):
        return weather_service.WeatherReading(
            location="Testville, Testland",
            temperature=21.5,
            apparent_temperature=20.0,
            wind_speed=11.0,
            weather_code=2,
            units=units,
        )

    monkeypatch.setattr(weather_service, "get_current_weather", fake_weather)
