"""SysMon options and history graph tests."""

import pytest
from pydantic import ValidationError

from termdash.widgets.sysmon import HistoryGraph, SysMonOptions


class TestSysMonOptions:
    @staticmethod
    def test_defaults():
        options = SysMonOptions()
        assert options.interval == 1.0
        assert options.history == 38

    @staticmethod
    @pytest.mark.parametrize("interval", [0, -1, 61])
    def test_interval_bounds(interval):
        with pytest.raises(ValidationError):
            SysMonOptions(interval=interval)

    @staticmethod
    @pytest.mark.parametrize("history", [0, 1, 201])
    def test_history_bounds(history):
        with pytest.raises(ValidationError):
            SysMonOptions(history=history)

    @staticmethod
    def test_boundary_values_are_accepted():
        options = SysMonOptions(interval=0.1, history=2)
        assert options.interval == 0.1
        assert options.history == 2
        options = SysMonOptions(interval=60, history=200)
        assert options.interval == 60
        assert options.history == 200


class TestHistoryGraph:
    @staticmethod
    def test_history_is_capped():
        graph = HistoryGraph(history=3)
        for value in (10.0, 20.0, 30.0, 40.0, 50.0):
            graph.record(value)
        assert graph.samples == [30.0, 40.0, 50.0]

    @staticmethod
    @pytest.mark.parametrize(
        ("value", "expected"),
        [
            (0, "green"),
            (59.9, "green"),
            (60, "yellow"),
            (84.9, "yellow"),
            (85, "red"),
            (100, "red"),
        ],
    )
    def test_default_cpu_thresholds(value, expected):
        graph = HistoryGraph()
        assert graph.colour_for(value) == expected

    @staticmethod
    def test_memory_thresholds_use_higher_limits():
        graph = HistoryGraph(green_below=80, yellow_below=95)
        assert graph.colour_for(79.9) == "green"
        assert graph.colour_for(80) == "yellow"
        assert graph.colour_for(95) == "red"

    @staticmethod
    @pytest.mark.parametrize(
        ("value", "expected"),
        [(150.0, 100.0), (-5.0, 0.0), (0.0, 0.0), (100.0, 100.0), (99.9, 99.9)],
    )
    def test_samples_clamp_to_percent_bounds(value, expected):
        graph = HistoryGraph(history=5)
        graph.record(value)
        assert graph.samples[-1] == expected

    @staticmethod
    def test_rendered_bars_use_block_characters():
        graph = HistoryGraph(history=4)
        graph.record(0.0)
        graph.record(100.0)
        assert graph.render_graph().plain == "▁█"
