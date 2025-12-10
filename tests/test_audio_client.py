import importlib.util
import sys
from pathlib import Path

import pyaudio
import pytest


MODULE_PATH = Path(__file__).resolve().parents[1] / "jobbie_gpt_CLIENT_05-10-2024.py"


class FakePyAudio:
    def __init__(self, supported_rates, default_rate):
        self.supported_rates = set(supported_rates)
        self.default_rate = default_rate

    def is_format_supported(
        self, rate, input_device=None, input_channels=None, input_format=None
    ):
        return rate in self.supported_rates

    def get_device_info_by_index(self, device_id):
        return {"defaultSampleRate": self.default_rate, "name": f"Fake {device_id}"}


def load_module(monkeypatch, fake_instance):
    """Load the audio client module with a patched PyAudio factory."""
    monkeypatch.setattr(pyaudio, "PyAudio", lambda: fake_instance)
    sys.modules.pop("jobbie_client", None)
    spec = importlib.util.spec_from_file_location("jobbie_client", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_resolve_pref_supported(monkeypatch):
    fake = FakePyAudio(supported_rates={16000, 32000}, default_rate=32000)
    module = load_module(monkeypatch, fake)

    rate, name = module.resolve_sample_rate(fake, 0, 1, pyaudio.paInt16, 16000)

    assert rate == 16000
    assert name == "Fake 0"


def test_resolve_falls_back_to_default(monkeypatch):
    fake = FakePyAudio(supported_rates={32000}, default_rate=32000)
    module = load_module(monkeypatch, fake)

    rate, _ = module.resolve_sample_rate(fake, 1, 1, pyaudio.paInt16, 44100)

    assert rate == 32000


def test_resolve_raises_when_unsupported(monkeypatch):
    fake = FakePyAudio(supported_rates=set(), default_rate=44100)
    module = load_module(monkeypatch, fake)

    with pytest.raises(ValueError):
        module.resolve_sample_rate(fake, 2, 1, pyaudio.paInt16, 48000)
