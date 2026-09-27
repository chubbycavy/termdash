"""Builder tests: how config nodes become positioned widgets."""

from termdash.builder import build_tree
from termdash.config import parse_config
from termdash.config.schema import WidgetNode
from termdash.widgets.clock import Clock
from termdash.widgets.invalid import InvalidWidget


def build(toml: str):
    config = parse_config(toml, source="test")
    assert config.root.valid, config.issues
    return build_tree(config.root)


def fr(dimension) -> float:
    """Read a fractional style dimension as its plain number."""
    assert dimension.unit.name == "FRACTION", dimension
    return dimension.value


def test_root_leaf_fills_the_screen():
    widget = build('[widgets]\nkind = "clock"\nopts = { timezone = "UTC" }\n')
    assert isinstance(widget, Clock)
    assert fr(widget.styles.width) == 1.0
    assert fr(widget.styles.height) == 1.0
    assert widget.timezone == "UTC"


def test_hbox_children_receive_width_weights():
    widget = build(
        """
        [widgets]
        kind = "hbox"

        [widgets.wide]
        kind = "clock"
        weight = 3

        [widgets.narrow]
        kind = "spacer"
        weight = 1
        """
    )
    wide, narrow = widget.elements
    assert fr(wide.styles.width) == 3.0
    assert fr(wide.styles.height) == 1.0
    assert fr(narrow.styles.width) == 1.0


def test_vbox_children_receive_height_weights():
    widget = build(
        """
        [widgets]
        kind = "vbox"

        [widgets.top]
        kind = "spacer"
        weight = 2

        [widgets.bottom]
        kind = "spacer"
        """
    )
    top, bottom = widget.elements
    assert fr(top.styles.height) == 2.0
    assert fr(top.styles.width) == 1.0
    assert fr(bottom.styles.height) == 1.0


def test_invalid_children_keep_their_weight_share():
    widget = build(
        """
        [widgets]
        kind = "hbox"

        [widgets.broken]
        kind = "clock"
        opts = { timezone = 10 }
        weight = 4

        [widgets.fine]
        kind = "spacer"
        """
    )
    warning, fine = widget.elements
    assert isinstance(warning, InvalidWidget)
    assert fr(warning.styles.width) == 4.0
    assert fr(fine.styles.width) == 1.0


def test_unknown_kind_node_becomes_a_warning():
    node = WidgetNode(kind="banana")
    widget = build_tree(node)
    assert isinstance(widget, InvalidWidget)
    assert "unknown widget 'banana'" in str(widget.render())


def test_invalid_root_node_becomes_a_warning():
    node = WidgetNode.invalid("widgets: everything is wrong")
    widget = build_tree(node)
    assert isinstance(widget, InvalidWidget)
    assert "everything is wrong" in str(widget.render())


def test_options_are_applied_to_widget_attributes():
    widget = build('[widgets]\nkind = "clock"\nopts = { timezone = "UTC" }\n')
    assert widget.timezone == "UTC"
    assert widget.label is None


def test_nested_containers_apply_weights_by_axis():
    widget = build(
        """
        [widgets]
        kind = "hbox"

        [widgets.column]
        kind = "vbox"
        weight = 2

        [widgets.column.a]
        kind = "spacer"
        weight = 3

        [widgets.column.b]
        kind = "spacer"
        """
    )
    column = widget.elements[0]
    assert fr(column.styles.width) == 2.0
    first, second = column.elements
    assert fr(first.styles.height) == 3.0
    assert fr(first.styles.width) == 1.0
    assert fr(second.styles.height) == 1.0
