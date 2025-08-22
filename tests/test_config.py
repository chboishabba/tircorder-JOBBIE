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
