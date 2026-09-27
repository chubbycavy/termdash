"""Service clients used by termdash widgets."""

from termdash.services.weather import (
    WeatherError,
    WeatherReading,
    get_current_weather,
    weather_label,
)

__all__ = [
    "WeatherError",
    "WeatherReading",
    "get_current_weather",
    "weather_label",
]
