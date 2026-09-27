"""CLI unit tests."""

import pytest

from termdash.cli import main, parse_size


class TestParseSize:
    @staticmethod
    @pytest.mark.parametrize(
        ("value", "expected"),
        [("120x36", (120, 36)), ("120X36", (120, 36)), (" 40x12 ", (40, 12))],
    )
    def test_valid_sizes(value, expected):
        assert parse_size(value) == expected

    @staticmethod
    @pytest.mark.parametrize(
        "value", ["bad", "120", "120x", "x36", "axb", "120x36x4"]
    )
    def test_malformed_sizes(value):
        with pytest.raises(ValueError, match="expected WxH"):
            parse_size(value)

    @staticmethod
    @pytest.mark.parametrize("value", ["1x1", "19x10", "20x9"])
    def test_too_small_sizes(value):
        with pytest.raises(ValueError, match="too small"):
            parse_size(value)


class TestCommands:
    @staticmethod
    def test_version_prints_and_exits_zero(capsys):
        assert main(["-V"]) == 0
        assert "termdash" in capsys.readouterr().out

        assert main(["--version"]) == 0
        assert "termdash" in capsys.readouterr().out

    @staticmethod
    def test_list_widgets_prints_the_registry(capsys):
        assert main(["list-widgets"]) == 0
        output = capsys.readouterr().out
        assert "clock" in output
        assert "todo" in output
        assert "timezone" in output

    @staticmethod
    def test_validate_accepts_the_packaged_default(capsys):
        assert main(["validate"]) == 0
        assert "OK" in capsys.readouterr().out

    @staticmethod
    def test_validate_reports_all_problems(capsys, tmp_path):
        broken = tmp_path / "broken.toml"
        broken.write_text(
            'theme = "neon"\n[widgets]\nkind = "banana"\n', encoding="utf-8"
        )

        assert main(["validate", "--config", str(broken)]) == 1
        output = capsys.readouterr().out
        assert "2 problem(s)" in output
        assert "unknown theme 'neon'" in output
        assert "unknown widget 'banana'" in output

    @staticmethod
    def test_validate_reports_an_unreadable_path(capsys, tmp_path):
        missing = tmp_path / "nope.toml"

        assert main(["validate", "--config", str(missing)]) == 1
        assert "cannot read" in capsys.readouterr().out
