"""Live weather tile backed by Open-Meteo."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field
from textual import work
from textual.app import ComposeResult
from textual.containers import HorizontalGroup, VerticalGroup
from textual.widgets import Button, Label, Static

from termdash.services import weather as weather_service
from termdash.widgets.common import TILE_CSS
from termdash.widgets.registry import register


class WeatherOptions(BaseModel):
    """Options for the weather widget."""

    model_config = ConfigDict(extra="forbid")

    location: str = Field(default="Sydney", min_length=1)
    units: Literal["metric", "imperial"] = "metric"
    refresh_minutes: int = Field(default=15, ge=1, le=1440)


@register("weather", WeatherOptions)
class Weather(VerticalGroup):
    """Current conditions with periodic automatic refresh."""

    location = "Sydney"
    units = "metric"
    refresh_minutes = 15

    DEFAULT_CSS = f"""
    Weather {{
        {TILE_CSS}
        align: center middle;
    }}

    Weather .weather-location,
    Weather .weather-current,
    Weather .weather-detail,
    Weather .weather-error,
    Weather .caption {{
        width: 100%;
        text-align: center;
    }}

    Weather .weather-location,
    Weather .caption {{
        color: $text-muted;
    }}

    Weather .weather-current {{
        text-style: bold;
    }}

    Weather .weather-error {{
        color: $error;
    }}

    Weather .controls {{
        width: 100%;
        height: 3;
        align: center middle;
    }}

    Weather .controls Button {{
        width: 1fr;
    }}

    Weather .caption {{
        text-style: bold;
    }}
    """

    def compose(self) -> ComposeResult:
        yield Label("", id="weather-location", classes="weather-location", markup=False)
        yield Static(
            "Loading weather...",
            id="weather-current",
            classes="weather-current",
            markup=False,
        )
        yield Static("", id="weather-detail", classes="weather-detail", markup=False)
        yield Static("", id="weather-error", classes="weather-error", markup=False)
        with HorizontalGroup(classes="controls"):
            yield Button("Refresh", id="weather-refresh")
        yield Label("Weather", classes="caption", markup=False)

    def on_mount(self) -> None:
        self.request_refresh()
        self.set_interval(self.refresh_minutes * 60, self.request_refresh)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "weather-refresh":
            self.request_refresh()

    def request_refresh(self) -> None:
        self.query_one("#weather-current", Static).update("Loading weather...")
        self.query_one("#weather-error", Static).update("")
        self.fetch_weather()

    @work(exclusive=True)
    async def fetch_weather(self) -> None:
        try:
            reading = await weather_service.get_current_weather(
                self.location, self.units
            )
        except weather_service.WeatherError as error:
            self.show_error(str(error))
        else:
            self.show_reading(reading)

    def show_reading(self, reading: weather_service.WeatherReading) -> None:
        degrees = "°F" if reading.units == "imperial" else "°C"
        wind = "mph" if reading.units == "imperial" else "km/h"
        self.query_one("#weather-location", Label).update(reading.location)
        self.query_one("#weather-current", Static).update(
            f"{reading.temperature:.0f}{degrees} · "
            f"{weather_service.weather_label(reading.weather_code)}"
        )
        self.query_one("#weather-detail", Static).update(
            f"Feels like {reading.apparent_temperature:.0f}{degrees} · "
            f"Wind {reading.wind_speed:.0f} {wind}"
        )

    def show_error(self, message: str) -> None:
        self.query_one("#weather-current", Static).update("Weather unavailable")
        self.query_one("#weather-error", Static).update(message)
