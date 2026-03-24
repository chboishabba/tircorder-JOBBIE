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

    def predict(self, **_kwargs: Any):
        raise RuntimeError("boom")


class _RejectTimeoutClient:
    attempts = []

    def __init__(self, base_url: str, **kwargs: Any) -> None:
        self.base_url = base_url
        self.init_kwargs = kwargs
        self.predict_kwargs: Optional[Dict[str, Any]] = None
        type(self).attempts.append(kwargs)
        if "timeout" in kwargs:
            raise TypeError("timeout not supported")

    def predict(self, **kwargs: Any):
        self.predict_kwargs = kwargs
        return ["recovered", 7.5]


class _FakeResponse:
    def __init__(self, payload: Dict[str, Any], status_code: int = 200) -> None:
        self._payload = payload
        self.status_code = status_code

    def json(self) -> Dict[str, Any]:
        return self._payload

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise RuntimeError(f"http {self.status_code}")


class _FakeSession:
    def __init__(self) -> None:
        self.auth = None
        self.headers: Dict[str, Any] = {}
        self.posts = []
        self.gets = []

    def __enter__(self) -> "_FakeSession":
        return self

    def __exit__(self, *_args: Any) -> None:
        return None

    def post(self, url: str, **kwargs: Any) -> _FakeResponse:
        self.posts.append((url, kwargs))
        return _FakeResponse({"identifier": "task-123", "status": "queued"}, status_code=201)

    def get(self, url: str, **kwargs: Any) -> _FakeResponse:
        self.gets.append((url, kwargs))
        return _FakeResponse(
            {
                "identifier": "task-123",
                "status": "completed",
                "result": {
                    "text": "backend hello",
                    "segments": [{"text": "backend hello", "start": 0.0, "end": 1.0}],
                    "model": "large-v3",
                    "language": "en",
                    "audio_duration": 4.5,
                },
            }
        )


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
    assert client.init_kwargs["timeout"] == 9.5
    assert transcript == "hello"
    assert duration == pytest.approx(3.2)
    assert metadata["error"] is None

    predict_kwargs = client.predict_kwargs
    assert predict_kwargs["api_name"] == "/_transcribe_file"
    assert predict_kwargs["files"] == [f"handled:{audio_file}"]
    assert predict_kwargs["whisper_hotwords"] == "[\"alpha\", \"beta\"]"
    assert "timeout" not in predict_kwargs


def test_transcribe_webui_retries_without_timeout(
    monkeypatch: pytest.MonkeyPatch, tmp_path
) -> None:
    _RejectTimeoutClient.attempts = []
    created: Dict[str, Any] = {}

    def _capture_client(*args: Any, **kwargs: Any) -> _RejectTimeoutClient:
        client = _RejectTimeoutClient(*args, **kwargs)
        created["client"] = client
        return client

    monkeypatch.setattr("tircorder.utils.Client", _capture_client)
    monkeypatch.setattr("tircorder.utils.handle_file", lambda path: f"handled:{path}")

    audio_file = tmp_path / "audio.wav"
    audio_file.write_bytes(b"RIFF")

    transcript, duration, metadata = transcribe_webui(
        str(audio_file),
        base_url="http://webui.local",
        timeout=3.0,
    )

    assert _RejectTimeoutClient.attempts[0]["timeout"] == 3.0
    assert _RejectTimeoutClient.attempts[-1] == {"ssl_verify": True}

    client = created["client"]
    assert client.init_kwargs == {"ssl_verify": True}
    assert transcript == "recovered"
    assert duration == pytest.approx(7.5)
    assert metadata["error"] is None

    predict_kwargs = client.predict_kwargs
    assert predict_kwargs["api_name"] == "/_transcribe_file"
    assert predict_kwargs["files"] == [f"handled:{audio_file}"]
    assert "timeout" not in predict_kwargs

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
    assert metadata["protocol"] == "gradio"
    assert metadata["transcript_payload"]["segments"] == []


def test_transcribe_webui_backend_success(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    created: Dict[str, Any] = {}

    def _capture_session() -> _FakeSession:
        session = _FakeSession()
        created["session"] = session
        return session

    monkeypatch.setattr("tircorder.utils.requests.Session", _capture_session)
    monkeypatch.setattr("tircorder.utils.time.sleep", lambda *_args, **_kwargs: None)

    audio_file = tmp_path / "audio.wav"
    audio_file.write_bytes(b"RIFF")

    transcript, duration, metadata = transcribe_webui(
        str(audio_file),
        base_url="http://webui.local",
        protocol="backend",
        backend_submit_path="/transcription",
        backend_task_path_template="/task/{identifier}",
        timeout=15.0,
        options={"whisper_hotwords": ["alpha", "beta"]},
        auth=("user", "pass"),
        headers={"X-Test": "1"},
        max_polls=1,
    )

    session = created["session"]
    assert session.auth == ("user", "pass")
    assert session.headers["X-Test"] == "1"
    assert transcript == "backend hello"
    assert duration == pytest.approx(4.5)
    assert metadata["protocol"] == "backend"
    assert metadata["task_id"] == "task-123"
    assert metadata["transcript_payload"]["model"] == "large-v3"

    post_url, post_kwargs = session.posts[0]
    assert post_url == "http://webui.local/transcription"
    assert post_kwargs["data"]["whisper_hotwords"] == "[\"alpha\", \"beta\"]"
    get_url, _get_kwargs = session.gets[0]
    assert get_url == "http://webui.local/task/task-123"


def test_get_transcription_backend_merges_defaults() -> None:
    TircorderConfig.set_config(
        {
            "transcription": {
                "method": "webui",
                "webui": {
                    "base_url": "http://example",
                    "protocol": "backend",
                    "backend": {
                        "poll_interval_seconds": 1.5,
                    },
                    "downstream": {
                        "sensiblaw": {
                            "enabled": True,
                        }
                    },
                },
            }
        }
    )

    method, backend = get_transcription_backend()

    assert method == "webui"
    assert backend["base_url"] == "http://example"
    assert backend["timeout"] == DEFAULT_WEBUI_CONFIG["timeout"]
    assert backend["protocol"] == "backend"
    assert backend["backend"]["poll_interval_seconds"] == 1.5
    assert backend["backend"]["task_path_template"] == "/task/{identifier}"
    assert backend["downstream"]["sensiblaw"]["enabled"] is True
    assert backend["downstream"]["statibaker"]["enabled"] is False
