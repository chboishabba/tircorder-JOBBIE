"""Tests for TircorderConfig persistence utilities."""

import json
import importlib.util
from pathlib import Path

import pytest

MODULE_PATH = (
    Path(__file__).resolve().parent.parent / "tircorder" / "interfaces" / "config.py"
)
SPEC = importlib.util.spec_from_file_location(
    "tircorder.interfaces.config", MODULE_PATH
)
config_module = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(config_module)
TircorderConfig = config_module.TircorderConfig


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


def test_get_config_returns_empty_when_missing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Missing config file should return an empty dictionary."""
    path = tmp_path / "missing.json"
    monkeypatch.setenv("TIRCORDER_CONFIG_PATH", str(path))

import importlib.util
from pathlib import Path

spec = importlib.util.spec_from_file_location(
    "tircorder.interfaces.config",
    Path(__file__).resolve().parent.parent / "tircorder" / "interfaces" / "config.py",
)
config_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(config_module)
TircorderConfig = config_module.TircorderConfig


def test_set_and_get_config(tmp_path, monkeypatch):
    config_path = tmp_path / "config.json"
    monkeypatch.setenv("TIRCORDER_CONFIG_PATH", str(config_path))

    data = {
        "api_base_url": "https://api.example.com",
        "export_format": "json",
        "output_path": str(tmp_path / "out"),
    }
    TircorderConfig.set_config(data)
    assert config_path.exists()

    loaded = TircorderConfig.get_config()
    assert loaded == data


def test_get_config_missing_file(tmp_path, monkeypatch):
    config_path = tmp_path / "config.json"
    monkeypatch.setenv("TIRCORDER_CONFIG_PATH", str(config_path))

    assert TircorderConfig.get_config() == {}
