"""Tests for the shipped default configuration."""

from pathlib import Path

from termdash.config import default_config_text, parse_config

REPO_ROOT = Path(__file__).resolve().parent.parent


def test_packaged_default_is_clean():
    config = parse_config(default_config_text(), source="packaged default")
    assert config.issues == []
    assert config.root.valid
    assert config.theme == "nord"


def test_repo_default_matches_packaged_default():
    repo_text = (REPO_ROOT / "defaults" / "termdash.toml").read_text(encoding="utf-8")
    assert repo_text == default_config_text()
