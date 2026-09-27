"""Weather service tests with a mocked HTTP transport."""

import asyncio
from types import SimpleNamespace

import httpx

from termdash.services import weather as weather_service

GEO_SYDNEY = {
    "results": [
        {
            "name": "Sydney",
            "latitude": -33.87,
            "longitude": 151.21,
            "country": "Australia",
        }
    ]
}

FORECAST_OK = {
    "current": {
        "temperature_2m": 21.6,
        "apparent_temperature": 20.1,
        "weather_code": 2,
        "wind_speed_10m": 12.34,
    }
}


def install_mock(monkeypatch, handler):
    """Swap the module's httpx for a stub whose client uses MockTransport."""

    def client_factory(**kwargs):
        kwargs.pop("timeout", None)
        return httpx.AsyncClient(transport=httpx.MockTransport(handler))

    monkeypatch.setattr(
        weather_service,
        "httpx",
        SimpleNamespace(AsyncClient=client_factory, HTTPError=httpx.HTTPError),
    )


def run(coro):
    return asyncio.run(coro)


def make_handler(forecast=FORECAST_OK, geo=GEO_SYDNEY, status=200):
    def handler(request: httpx.Request) -> httpx.Response:
        if "geocoding" in str(request.url):
            return httpx.Response(status, json=geo)
        return httpx.Response(status, json=forecast)

    return handler


def test_happy_path_returns_a_reading(monkeypatch):
    install_mock(monkeypatch, make_handler())

    reading = run(weather_service.get_current_weather("Sydney", "metric"))

    assert reading.location == "Sydney, Australia"
    assert reading.temperature == 21.6
    assert reading.apparent_temperature == 20.1
    assert reading.wind_speed == 12.34
    assert reading.weather_code == 2
    assert reading.units == "metric"


def test_imperial_uses_fahrenheit_and_mph(monkeypatch):
    captured = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured.setdefault(str(request.url), None)
        return make_handler()(request)

    install_mock(monkeypatch, handler)

    reading = run(weather_service.get_current_weather("Sydney", "imperial"))

    assert reading.units == "imperial"
    assert any("temperature_unit=fahrenheit" in url for url in captured)
    assert any("wind_speed_unit=mph" in url for url in captured)


def test_metric_uses_celsius_and_kmh(monkeypatch):
    captured = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured.setdefault(str(request.url), None)
        return make_handler()(request)

    install_mock(monkeypatch, handler)

    run(weather_service.get_current_weather("Sydney", "metric"))

    assert any("temperature_unit=celsius" in url for url in captured)
    assert any("wind_speed_unit=kmh" in url for url in captured)


def test_unknown_location_raises(monkeypatch):
    install_mock(monkeypatch, make_handler(geo={"results": []}))

    try:
        run(weather_service.get_current_weather("Nowhere", "metric"))
    except weather_service.WeatherError as error:
        assert "Location not found: Nowhere" in str(error)
    else:
        raise AssertionError("expected WeatherError")


def test_http_error_is_wrapped(monkeypatch):
    install_mock(monkeypatch, make_handler(status=500))

    try:
        run(weather_service.get_current_weather("Sydney", "metric"))
    except weather_service.WeatherError as error:
        assert "Weather request failed" in str(error)
    else:
        raise AssertionError("expected WeatherError")


def test_malformed_forecast_is_wrapped(monkeypatch):
    install_mock(monkeypatch, make_handler(forecast={"current": {}}))

    try:
        run(weather_service.get_current_weather("Sydney", "metric"))
    except weather_service.WeatherError as error:
        assert "Unexpected weather response" in str(error)
    else:
        raise AssertionError("expected WeatherError")


def test_weather_labels_cover_common_codes():
    assert weather_service.weather_label(0) == "Clear"
    assert weather_service.weather_label(3) == "Overcast"
    assert weather_service.weather_label(45) == "Fog"
    assert weather_service.weather_label(63) == "Rain"
    assert weather_service.weather_label(73) == "Snow"
    assert weather_service.weather_label(95) == "Thunderstorm"
    assert weather_service.weather_label(4242) == "Unknown"
