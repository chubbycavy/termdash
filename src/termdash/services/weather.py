"""Async Open-Meteo weather client (no API key required)."""

from __future__ import annotations

from dataclasses import dataclass

import httpx

GEOCODE_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"

WMO_LABELS: dict[int, str] = {
    0: "Clear",
    1: "Mostly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Fog",
    48: "Rime fog",
    51: "Light drizzle",
    53: "Drizzle",
    55: "Heavy drizzle",
    56: "Freezing drizzle",
    57: "Freezing drizzle",
    61: "Light rain",
    63: "Rain",
    65: "Heavy rain",
    66: "Freezing rain",
    67: "Freezing rain",
    71: "Light snow",
    73: "Snow",
    75: "Heavy snow",
    77: "Snow grains",
    80: "Light showers",
    81: "Showers",
    82: "Heavy showers",
    85: "Snow showers",
    86: "Heavy snow showers",
    95: "Thunderstorm",
    96: "Thunderstorm, hail",
    99: "Thunderstorm, hail",
}


class WeatherError(Exception):
    """Raised when weather cannot be fetched or understood."""


@dataclass(frozen=True)
class WeatherReading:
    """One current-conditions reading."""

    location: str
    temperature: float
    apparent_temperature: float
    wind_speed: float
    weather_code: int
    units: str


def weather_label(code: int) -> str:
    """Translate a WMO weather code into a short label."""
    return WMO_LABELS.get(code, "Unknown")


async def get_current_weather(
    location: str, units: str, *, timeout: float = 8.0
) -> WeatherReading:
    """Fetch current conditions for a location via Open-Meteo."""
    temperature_unit = "fahrenheit" if units == "imperial" else "celsius"
    wind_unit = "mph" if units == "imperial" else "kmh"
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            geocode = await client.get(
                GEOCODE_URL,
                params={
                    "name": location,
                    "count": 1,
                    "language": "en",
                    "format": "json",
                },
            )
            geocode.raise_for_status()
            results = geocode.json().get("results") or []
            if not results:
                raise WeatherError(f"Location not found: {location}")
            place = results[0]
            forecast = await client.get(
                FORECAST_URL,
                params={
                    "latitude": place["latitude"],
                    "longitude": place["longitude"],
                    "current": (
                        "temperature_2m,apparent_temperature,"
                        "weather_code,wind_speed_10m"
                    ),
                    "temperature_unit": temperature_unit,
                    "wind_speed_unit": wind_unit,
                    "timezone": "auto",
                },
            )
            forecast.raise_for_status()
            current = forecast.json().get("current") or {}
    except WeatherError:
        raise
    except httpx.HTTPError as error:
        raise WeatherError(f"Weather request failed: {error}") from error

    try:
        return WeatherReading(
            location=f"{place['name']}, {place.get('country', '')}".strip(", "),
            temperature=float(current["temperature_2m"]),
            apparent_temperature=float(current["apparent_temperature"]),
            wind_speed=float(current["wind_speed_10m"]),
            weather_code=int(current["weather_code"]),
            units=units,
        )
    except (KeyError, TypeError, ValueError) as error:
        raise WeatherError("Unexpected weather response") from error
