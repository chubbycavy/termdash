"""Tests for the widget registry."""

from termdash.widgets import REGISTRY, available_kinds, lookup


def test_expected_kinds_are_registered():
    assert set(REGISTRY) >= {
        "hbox",
        "vbox",
        "clock",
        "timer",
        "stopwatch",
        "sysmon",
        "weather",
        "spacer",
    }


def test_lookup_is_case_insensitive():
    entry = lookup("Clock")
    assert entry is not None
    assert entry.kind == "clock"
    assert lookup("nope") is None


def test_containers_are_flagged():
    assert lookup("hbox").container
    assert lookup("vbox").container
    assert not lookup("clock").container


def test_available_kinds_is_sorted():
    kinds = available_kinds()
    assert kinds == sorted(kinds)
