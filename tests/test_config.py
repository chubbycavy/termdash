"""Tests for TOML configuration parsing and validation."""

from termdash.config import parse_config
from termdash.widgets.clock import ClockOptions


def parse(text: str):
    return parse_config(text, source="test")


def test_valid_tree_with_weights():
    config = parse(
        """
        theme = "nord"

        [widgets]
        kind = "hbox"

        [widgets.left]
        kind = "vbox"
        weight = 2

        [widgets.left.clock]
        kind = "Clock"
        opts = { timezone = "UTC" }
        """
    )
    assert config.issues == []
    assert config.theme == "nord"
    assert config.root.kind == "hbox"
    left = config.root.children[0]
    assert left.kind == "vbox"
    assert left.weight == 2.0
    clock = left.children[0]
    assert clock.kind == "clock"
    assert isinstance(clock.options, ClockOptions)
    assert clock.options.timezone == "UTC"


def test_kinds_are_case_insensitive():
    config = parse('[widgets]\nkind = "HBox"\n')
    assert config.issues == []
    assert config.root.kind == "hbox"


def test_unknown_widget_lists_available_kinds():
    config = parse('[widgets]\nkind = "banana"\n')
    assert not config.root.valid
    issue = config.issues[0]
    assert "unknown widget 'banana'" in issue
    assert "available:" in issue
    assert "clock" in issue


def test_unknown_option_lists_valid_options():
    config = parse('[widgets]\nkind = "clock"\nopts = { frobnicate = true }\n')
    assert not config.root.valid
    issue = config.issues[0]
    assert "unknown option 'frobnicate'" in issue
    assert "valid options: label, timezone" in issue


def test_option_type_error_mentions_the_field():
    config = parse('[widgets]\nkind = "clock"\nopts = { timezone = 10 }\n')
    assert not config.root.valid
    assert "option 'timezone'" in config.issues[0]


def test_invalid_timezone_value_is_reported():
    config = parse(
        '[widgets]\nkind = "clock"\nopts = { timezone = "Mars/Olympus" }\n'
    )
    assert not config.root.valid
    assert "unknown timezone" in config.issues[0]


def test_widget_without_options_rejects_any_option():
    config = parse('[widgets]\nkind = "stopwatch"\nopts = { beep = true }\n')
    assert not config.root.valid
    assert "unknown option 'beep'" in config.issues[0]
    assert "valid options: none" in config.issues[0]


def test_leaf_cannot_contain_children():
    config = parse(
        """
        [widgets]
        kind = "clock"

        [widgets.oops]
        kind = "timer"
        """
    )
    assert not config.root.valid
    assert "cannot contain child tables" in config.issues[0]


def test_invalid_weight_is_reported():
    config = parse('[widgets]\nkind = "clock"\nweight = -1\n')
    assert not config.root.valid
    assert "weight must be a positive number" in config.issues[0]


def test_unknown_theme_is_reported_but_app_still_loads():
    config = parse('theme = "neon"\n[widgets]\nkind = "clock"\n')
    assert config.theme == "dark"
    assert any("unknown theme 'neon'" in issue for issue in config.issues)
    assert config.root.valid


def test_unknown_top_level_key_is_reported():
    config = parse('widgest = 3\n[widgets]\nkind = "clock"\n')
    assert any("unknown top-level key 'widgest'" in issue for issue in config.issues)
    assert config.root.valid


def test_missing_widgets_table_is_a_root_error():
    config = parse('theme = "nord"\n')
    assert not config.root.valid
    assert "[widgets]" in config.issues[0]


def test_malformed_toml_is_a_root_error():
    config = parse("[widgets\nkind =")
    assert not config.root.valid
    assert "TOML parse error" in config.issues[0]


def test_opts_must_be_a_table():
    config = parse('[widgets]\nkind = "clock"\nopts = "beep"\n')
    assert not config.root.valid
    assert "opts must be a table" in config.issues[0]


def test_stray_keys_are_reported():
    config = parse('[widgets]\nkind = "clock"\ncolour = "red"\n')
    assert not config.root.valid
    assert "unknown key(s)" in config.issues[0]
    assert "'colour'" in config.issues[0]


def test_child_errors_include_their_path():
    config = parse(
        """
        [widgets]
        kind = "hbox"

        [widgets.left]
        kind = "clock"
        opts = { frobnicate = 1 }
        """
    )
    assert config.issues[0].startswith("widgets.left:")
    assert not config.root.children[0].valid


def test_children_are_parsed_even_if_sibling_is_broken():
    config = parse(
        """
        [widgets]
        kind = "hbox"

        [widgets.bad]
        kind = "clock"
        opts = { frobnicate = 1 }

        [widgets.also_bad]
        kind = "nope"
        """
    )
    assert len(config.issues) == 2


def test_boolean_weight_is_rejected():
    config = parse('[widgets]\nkind = "clock"\nweight = true\n')
    assert not config.root.valid
    assert "positive number" in config.issues[0]


def test_string_weight_is_rejected():
    config = parse('[widgets]\nkind = "clock"\nweight = "2"\n')
    assert not config.root.valid
    assert "positive number" in config.issues[0]


def test_fractional_weight_is_accepted():
    config = parse('[widgets]\nkind = "clock"\nweight = 1.5\n')
    assert config.root.valid
    assert config.root.weight == 1.5


def test_root_may_be_a_leaf_widget():
    config = parse('[widgets]\nkind = "clock"\nopts = { timezone = "UTC" }\n')
    assert config.issues == []
    assert config.root.valid
    assert config.root.children == []


def test_kind_whitespace_is_trimmed():
    config = parse('[widgets]\nkind = "  clock  "\n')
    assert config.issues == []
    assert config.root.kind == "clock"


def test_blank_kind_is_rejected():
    config = parse('[widgets]\nkind = ""\n')
    assert not config.root.valid
    assert "missing or invalid 'kind'" in config.issues[0]


def test_empty_theme_is_reported():
    config = parse('theme = ""\n[widgets]\nkind = "clock"\n')
    assert config.theme == "dark"
    assert any("unknown theme" in issue for issue in config.issues)
    assert config.root.valid


def test_all_issues_report_paths_from_the_whole_tree():
    config = parse(
        """
        theme = "neon"

        [widgets]
        kind = "hbox"

        [widgets.a]
        kind = "nope"

        [widgets.b]
        kind = "timer"
        weight = -1
        """
    )
    paths = [issue.split(":")[0] for issue in config.issues]
    assert "theme" in paths
    assert "widgets.a" in paths
    assert "widgets.b" in paths
    assert len(config.issues) >= 3
