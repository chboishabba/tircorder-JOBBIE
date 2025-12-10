from typing import Any, Dict, Optional

import pytest

pytest.importorskip("librosa")
pytest.importorskip("requests")

from tircorder.interfaces.config import TircorderConfig
from tircorder.utils import (
    DEFAULT_WEBUI_CONFIG,
    get_transcription_backend,
    transcribe_webui,
)


class _FakeClient:
    def __init__(self, base_url: str, **kwargs: Any) -> None:
        self.base_url = base_url
        self.init_kwargs = kwargs
        self.predict_kwargs: Optional[Dict[str, Any]] = None

    def predict(self, **kwargs: Any):
        self.predict_kwargs = kwargs
        return ["hello", 3.2]

class _FailingClient:
    def __init__(self, *_args: Any, **_kwargs: Any) -> None:
        pass

class _FailingClient:
    def __init__(self, *_args: Any, **_kwargs: Any) -> None:
        pass

    def predict(self, **_kwargs: Any):
        raise RuntimeError("boom")


@pytest.fixture(autouse=True)
def reset_config(tmp_path, monkeypatch: pytest.MonkeyPatch):
    config_path = tmp_path / "config.json"
    monkeypatch.setenv("TIRCORDER_CONFIG_PATH", str(config_path))
    yield


def test_transcribe_webui_success(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    created: Dict[str, Any] = {}

    def _capture_client(*args: Any, **kwargs: Any) -> _FakeClient:
        client = _FakeClient(*args, **kwargs)
        created["client"] = client
        return client

    monkeypatch.setattr("tircorder.utils.Client", _capture_client)
    monkeypatch.setattr("tircorder.utils.handle_file", lambda path: f"handled:{path}")

    audio_file = tmp_path / "audio.wav"
    audio_file.write_bytes(b"RIFF")

    transcript, duration, metadata = transcribe_webui(
        str(audio_file),
        base_url="http://webui.local",
        transcribe_path="/_transcribe_file",
        timeout=9.5,
        options={"whisper_hotwords": ["alpha", "beta"]},
        auth=("user", "pass"),
        headers={"X-Test": "1"},
    )

    client = created["client"]
    assert client.base_url == "http://webui.local"
    assert client.init_kwargs["auth"] == ("user", "pass")
    assert client.init_kwargs["headers"] == {"X-Test": "1"}
    assert transcript == "hello"
    assert duration == pytest.approx(3.2)
    assert metadata["error"] is None

    predict_kwargs = client.predict_kwargs
    assert predict_kwargs["api_name"] == "/_transcribe_file"
    assert predict_kwargs["timeout"] == 9.5
    assert predict_kwargs["files"] == [f"handled:{audio_file}"]
    assert predict_kwargs["whisper_hotwords"] == "[\"alpha\", \"beta\"]"

    predict_kwargs = client.predict_kwargs
    assert predict_kwargs["api_name"] == "/_transcribe_file"
    assert predict_kwargs["timeout"] == 9.5
    assert predict_kwargs["files"] == [f"handled:{audio_file}"]
    assert predict_kwargs["whisper_hotwords"] == "[\"alpha\", \"beta\"]"


def test_transcribe_webui_retries_without_timeout(
    monkeypatch: pytest.MonkeyPatch, tmp_path
) -> None:
    created: Dict[str, Any] = {}

    def _capture_client(*args: Any, **kwargs: Any) -> _RejectTimeoutClient:
        client = _RejectTimeoutClient(*args, **kwargs)
        created["client"] = client
        return client

    monkeypatch.setattr("tircorder.utils.Client", _capture_client)
    monkeypatch.setattr("tircorder.utils.handle_file", lambda path: f"handled:{path}")

def test_transcribe_webui_handles_exceptions(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    monkeypatch.setattr("tircorder.utils.Client", _FailingClient)
    audio_file = tmp_path / "audio.wav"
    audio_file.write_bytes(b"RIFF")

    transcript, duration, metadata = transcribe_webui(
        str(audio_file),
        base_url="http://webui.local",
    )

    assert transcript is None
    assert duration == 0.0
    assert metadata["error"] == "boom"


def test_get_transcription_backend_merges_defaults() -> None:
    TircorderConfig.set_config(
        {
            "transcription": {
                "method": "webui",
                "webui": {
                    "base_url": "http://example",
                    "poll_interval": 1.5,
                },
            }
        }
    )

    method, backend = get_transcription_backend()

    assert method == "webui"
    assert backend["base_url"] == "http://example"
    assert backend["timeout"] == DEFAULT_WEBUI_CONFIG["timeout"]
    assert backend["poll_interval"] == 1.5
