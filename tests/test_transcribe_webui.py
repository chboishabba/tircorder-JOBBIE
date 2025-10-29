"""Tests for the Whisper-WebUI transcription helper."""

from __future__ import annotations

from typing import Any, Dict, Iterable, List

import pytest

pytest.importorskip("librosa")
pytest.importorskip("requests")

from tircorder.interfaces.config import TircorderConfig
from tircorder.utils import (
    DEFAULT_WEBUI_CONFIG,
    get_transcription_backend,
    transcribe_webui,
)


class _DummyResponse:
    def __init__(self, payload: Dict[str, Any], status_code: int = 200) -> None:
        self._payload = payload
        self.status_code = status_code

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")

    def json(self) -> Dict[str, Any]:
        return self._payload


class _MockSession:
    def __init__(self, post_response: _DummyResponse, get_responses: Iterable[_DummyResponse]) -> None:
        self.post_response = post_response
        self.get_responses = list(get_responses)
        self.post_calls: List[Dict[str, Any]] = []
        self.get_calls: List[Dict[str, Any]] = []

    def post(self, *args: Any, **kwargs: Any) -> _DummyResponse:
        self.post_calls.append({"args": args, "kwargs": kwargs})
        return self.post_response

    def get(self, *args: Any, **kwargs: Any) -> _DummyResponse:
        self.get_calls.append({"args": args, "kwargs": kwargs})
        if not self.get_responses:
            raise AssertionError("No more mocked responses available")
        return self.get_responses.pop(0)


def _mock_monotonic(sequence: Iterable[float]):
    iterator = iter(sequence)

    def _inner() -> float:
        return next(iterator)

    return _inner


def test_transcribe_webui_success(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    audio_file = tmp_path / "audio.wav"
    audio_file.write_bytes(b"RIFF")

    session = _MockSession(
        _DummyResponse({"task_id": "abc123"}),
        [
            _DummyResponse({"status": "in_progress"}),
            _DummyResponse(
                {
                    "status": "completed",
                    "result": [{"text": "hello", "start": 0, "end": 1.0}],
                    "duration": 3.2,
                }
            ),
        ],
    )

    monkeypatch.setattr("tircorder.utils.time.sleep", lambda _seconds: None)
    monkeypatch.setattr(
        "tircorder.utils.time.monotonic",
        _mock_monotonic([0.0, 1.0, 2.0, 3.0]),
    )

    transcript, duration, metadata = transcribe_webui(
        str(audio_file),
        base_url="http://webui.local",
        poll_interval=0.1,
        timeout=10.0,
        session=session,
    )

    assert transcript == "[0.00s -> 1.00s] hello"
    assert duration == pytest.approx(3.2)
    assert metadata["task_id"] == "abc123"
    assert metadata["error"] is None
    assert session.post_calls, "Expected the helper to invoke POST"
    assert session.get_calls, "Expected the helper to poll task status"


def test_transcribe_webui_failure(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    audio_file = tmp_path / "audio.wav"
    audio_file.write_bytes(b"RIFF")

    session = _MockSession(
        _DummyResponse({"task_id": "xyz"}),
        [_DummyResponse({"status": "failed", "error": "boom", "duration": 1.5})],
    )

    monkeypatch.setattr("tircorder.utils.time.sleep", lambda _seconds: None)
    monkeypatch.setattr(
        "tircorder.utils.time.monotonic",
        _mock_monotonic([0.0, 1.0, 2.0]),
    )

    transcript, duration, metadata = transcribe_webui(
        str(audio_file),
        base_url="http://webui.local",
        poll_interval=0.1,
        timeout=5.0,
        session=session,
    )

    assert transcript is None
    assert duration == pytest.approx(1.5)
    assert metadata["error"] == "boom"


def test_get_transcription_backend_merges_defaults(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    config_path = tmp_path / "config.json"
    monkeypatch.setenv("TIRCORDER_CONFIG_PATH", str(config_path))

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
    assert backend["poll_interval"] == 1.5
    assert backend["timeout"] == DEFAULT_WEBUI_CONFIG["timeout"]
