"""Tests for TircorderConfig persistence utilities."""

import json
from pathlib import Path

import pytest

from tircorder.interfaces.config import TircorderConfig


def test_set_and_get_config(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Configuration values should persist to disk and be retrievable."""
    path = tmp_path / "config.json"
    monkeypatch.setenv("TIRCORDER_CONFIG_PATH", str(path))
    data = {
        "api_base_url": "https://api.example.com",
        "export_format": "json",
        "output_path": "/tmp/output",
    }
    TircorderConfig.set_config(data)
    assert path.exists()
    with path.open("r", encoding="utf-8") as handle:
        assert json.load(handle) == data
    assert TircorderConfig.get_config() == data


def test_get_config_missing_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Missing config file should return an empty dictionary."""
    path = tmp_path / "missing.json"
    monkeypatch.setenv("TIRCORDER_CONFIG_PATH", str(path))
    assert TircorderConfig.get_config() == {}
