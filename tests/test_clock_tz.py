"""Timezone resolution tests for the clock widget."""

from datetime import UTC, timezone
from zoneinfo import ZoneInfo

import pytest
from pydantic import ValidationError

from termdash.widgets.clock import ClockOptions, resolve_timezone


class TestResolveTimezone:
    @staticmethod
    def test_local_resolves_to_none():
        assert resolve_timezone("local") is None
        assert resolve_timezone("  LOCAL  ") is None

    @staticmethod
    @pytest.mark.parametrize("value", ["UTC", "utc", "Utc", "UTC+0"])
    def test_utc_variants_resolve_to_utc(value):
        assert resolve_timezone(value) == UTC

    @staticmethod
    @pytest.mark.parametrize(
        ("value", "hours"),
        [("UTC+2", 2), ("UTC-5.5", -5.5), ("UTC+0.5", 0.5)],
    )
    def test_offsets_resolve_to_fixed_timezones(value, hours):
        from datetime import timedelta

        assert resolve_timezone(value) == timezone(timedelta(hours=hours))

    @staticmethod
    def test_iana_names_resolve_to_zoneinfo():
        zone = resolve_timezone("Europe/Berlin")
        assert isinstance(zone, ZoneInfo)
        assert zone.key == "Europe/Berlin"

    @staticmethod
    def test_unknown_iana_name_raises_with_guidance():
        with pytest.raises(ValueError, match="unknown timezone 'Mars/Olympus'"):
            resolve_timezone("Mars/Olympus")

    @staticmethod
    def test_malformed_offset_raises():
        with pytest.raises(ValueError, match="UTC\\+2"):
            resolve_timezone("UTC+x")

    @staticmethod
    def test_out_of_range_offset_raises():
        with pytest.raises(ValueError, match="-24 and 24"):
            resolve_timezone("UTC+33")


class TestClockOptions:
    @staticmethod
    def test_defaults_are_local_and_label_free():
        options = ClockOptions()
        assert options.timezone == "local"
        assert options.label is None

    @staticmethod
    def test_valid_options_are_accepted():
        options = ClockOptions(timezone="Australia/Sydney", label="HQ")
        assert options.timezone == "Australia/Sydney"
        assert options.label == "HQ"

    @staticmethod
    def test_invalid_timezone_rejected_with_message():
        with pytest.raises(ValidationError) as excinfo:
            ClockOptions(timezone="Nowhere/City")
        assert "unknown timezone 'Nowhere/City'" in str(excinfo.value)

    @staticmethod
    def test_unknown_option_rejected():
        with pytest.raises(ValidationError, match="frobnicate"):
            ClockOptions(frobnicate=True)
