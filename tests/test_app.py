"""Application-level rendering tests."""

from conftest import freeze_environment, run_pilot
from textual.containers import Container
from textual.widgets import Static

from termdash.app import Termdash
from termdash.config import default_config_text, parse_config
from termdash.widgets.clock import Clock
from termdash.widgets.invalid import InvalidWidget
from termdash.widgets.timer import Timer


def test_default_layout_renders_every_widget(monkeypatch):
    freeze_environment(monkeypatch)
    config = parse_config(default_config_text(), source="test")

    async def scenario(pilot):
        assert len(pilot.app.query(Clock)) == 1
        assert len(pilot.app.query(Timer)) == 1
        assert len(pilot.app.query(InvalidWidget)) == 0

    run_pilot(Termdash(config), scenario)


def test_invalid_root_shows_warning_screen():
    config = parse_config('[widgets]\nkind = "banana"\n', source="test")

    async def scenario(pilot):
        screen = pilot.app.query_one("#config-warning-screen", Container)
        warning = pilot.app.query_one("#config-warning", Static)
        text = str(warning.render())
        assert screen is not None
        assert "unknown widget 'banana'" in text
        assert "termdash validate" in text

    run_pilot(Termdash(config), scenario)


def test_invalid_child_becomes_a_warning_tile(monkeypatch):
    freeze_environment(monkeypatch)
    config = parse_config(
        """
        [widgets]
        kind = "hbox"

        [widgets.good]
        kind = "clock"
        opts = { timezone = "UTC" }

        [widgets.bad]
        kind = "clock"
        opts = { timezone = 10 }
        """,
        source="test",
    )

    async def scenario(pilot):
        good = pilot.app.query_one(Clock)
        tiles = pilot.app.query(InvalidWidget)
        assert len(tiles) == 1
        warning = tiles.first()
        text = str(warning.render())
        assert "option 'timezone'" in text
        assert good.region.width > 0
        assert warning.region.width > 0
        assert abs(good.region.width - warning.region.width) <= 2

    run_pilot(Termdash(config), scenario)


def test_theme_from_config_is_applied():
    config = parse_config(
        'theme = "gruvbox"\n[widgets]\nkind = "spacer"\n', source="test"
    )

    async def scenario(pilot):
        assert pilot.app.theme == "gruvbox"

    run_pilot(Termdash(config), scenario)
