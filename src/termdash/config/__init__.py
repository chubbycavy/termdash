"""Configuration loading and validation for termdash."""

from termdash.config.loader import (
    CONFIG_ENV_VAR,
    default_config_text,
    find_config_path,
    load_config,
    parse_config,
)
from termdash.config.schema import INVALID_KIND, ParsedConfig, WidgetNode

__all__ = [
    "CONFIG_ENV_VAR",
    "INVALID_KIND",
    "ParsedConfig",
    "WidgetNode",
    "default_config_text",
    "find_config_path",
    "load_config",
    "parse_config",
]
