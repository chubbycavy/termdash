"""Command-line interface for termdash."""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

from termdash import __version__

COMMANDS = {"run", "validate", "list-widgets", "screenshot"}


def main(argv: list[str] | None = None) -> int:
    """Run the requested subcommand; default to 'run'."""
    args = list(sys.argv[1:] if argv is None else argv)
    if args and args[0] in {"-V", "--version"}:
        print(f"termdash {__version__}")
        return 0
    if not args or (
        args[0] not in COMMANDS and args[0] not in {"-h", "--help"}
    ):
        args = ["run", *args]
    parser = build_parser()
    namespace = parser.parse_args(args)
    if namespace.command == "run":
        return command_run(namespace)
    if namespace.command == "validate":
        return command_validate(namespace)
    if namespace.command == "list-widgets":
        return command_list_widgets()
    return command_screenshot(namespace)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="termdash",
        description="A configurable terminal dashboard.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    run = sub.add_parser("run", help="run the dashboard (Ctrl+Q to quit)")
    run.add_argument("--config", "-c", type=Path, help="path to termdash.toml")

    validate = sub.add_parser("validate", help="check the configuration")
    validate.add_argument("--config", "-c", type=Path, help="path to termdash.toml")

    sub.add_parser("list-widgets", help="show every widget and its options")

    screenshot = sub.add_parser(
        "screenshot", help="render one frame of the dashboard to SVG"
    )
    screenshot.add_argument("--config", "-c", type=Path, help="path to termdash.toml")
    screenshot.add_argument(
        "--output",
        "-o",
        type=Path,
        default=Path("termdash.svg"),
        help="output SVG path",
    )
    screenshot.add_argument(
        "--size", default="120x36", metavar="WxH", help="terminal size (default 120x36)"
    )
    screenshot.add_argument(
        "--wait",
        type=float,
        default=1.5,
        metavar="SECONDS",
        help="seconds to let widgets settle before capturing",
    )
    return parser


def command_run(namespace: argparse.Namespace) -> int:
    from termdash.app import Termdash
    from termdash.config import load_config

    config = load_config(namespace.config)
    for issue in config.issues:
        print(f"termdash: warning: {issue}", file=sys.stderr)
    exit_code = Termdash(config).run()
    return int(exit_code) if exit_code is not None else 0


def command_validate(namespace: argparse.Namespace) -> int:
    from termdash.config import load_config

    config = load_config(namespace.config)
    if config.issues:
        count = len(config.issues)
        print(f"termdash: {count} problem(s) in {config.source}")
        for issue in config.issues:
            print(f"  - {issue}")
        return 1
    print(f"OK: {config.source}")
    return 0


def command_list_widgets() -> int:
    from termdash.widgets import REGISTRY

    print(f"{'kind':<12} {'options':<34} description")
    print(f"{'----':<12} {'-------':<34} -----------")
    for key in sorted(REGISTRY):
        entry = REGISTRY[key]
        if entry.container:
            options = "(child tables)"
        elif entry.options.model_fields:
            options = ", ".join(sorted(entry.options.model_fields))
        else:
            options = "-"
        doc = entry.widget_cls.__doc__ or ""
        description = doc.strip().splitlines()[0] if doc.strip() else ""
        print(f"{key:<12} {options:<34} {description}")
    return 0


def command_screenshot(namespace: argparse.Namespace) -> int:
    from termdash.app import Termdash
    from termdash.config import load_config

    try:
        width, height = parse_size(namespace.size)
    except ValueError as error:
        print(f"termdash: {error}", file=sys.stderr)
        return 2

    config = load_config(namespace.config)
    for issue in config.issues:
        print(f"termdash: warning: {issue}", file=sys.stderr)
    app = Termdash(config)

    async def capture() -> None:
        async with app.run_test(size=(width, height)) as pilot:
            await pilot.pause(namespace.wait)
            app.save_screenshot(str(namespace.output))

    asyncio.run(capture())
    print(f"saved {namespace.output}")
    return 0


def parse_size(value: str) -> tuple[int, int]:
    text = value.lower().replace(" ", "")
    if "x" not in text:
        raise ValueError(f"invalid size '{value}': expected WxH, e.g. 120x36")
    width_text, height_text = text.split("x", 1)
    try:
        width, height = int(width_text), int(height_text)
    except ValueError as error:
        raise ValueError(
            f"invalid size '{value}': expected WxH, e.g. 120x36"
        ) from error
    if width < 20 or height < 10:
        raise ValueError(f"size '{value}' is too small (min 20x10)")
    return width, height


if __name__ == "__main__":
    sys.exit(main())
