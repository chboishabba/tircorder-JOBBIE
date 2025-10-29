import sys
import types
from pathlib import Path

import pytest

sys.modules.setdefault("librosa", types.ModuleType("librosa"))

from tircorder.utils import transcribe_webui


class DummySession:
    def __init__(self):
        self.calls = []

    def post(self, url, **kwargs):
        self.calls.append((url, kwargs))
        return types.SimpleNamespace(status_code=201)


@pytest.fixture()
def audio_file(tmp_path: Path) -> Path:
    path = tmp_path / "sample.wav"
    path.write_bytes(b"RIFF....WAVE")
    return path


def test_transcribe_webui_posts_to_transcription_endpoint(audio_file: Path):
    session = DummySession()
    options = {
        "whisper": {
            "model_size": "small",
            "compute_type": "int8",
            "enable_offload": True,
        },
        "vad": {"vad_filter": True},
        "bgm_separation": {"is_separate_bgm": False},
        "diarization": {"is_diarize": True, "diarization_device": "cpu"},
    }

    response = transcribe_webui(
        "https://example.com/api",
        str(audio_file),
        options=options,
        timeout=12,
        session=session,
    )

    assert response.status_code == 201
    assert len(session.calls) == 1

    url, kwargs = session.calls[0]
    assert url == "https://example.com/api/transcription"

    data = kwargs["data"]
    assert data["whisper.model_size"] == "small"
    assert data["whisper.compute_type"] == "int8"
    assert data["whisper.enable_offload"] is True
    assert data["vad.vad_filter"] is True
    assert data["bgm_separation.is_separate_bgm"] is False
    assert data["diarization.is_diarize"] is True
    assert data["diarization.diarization_device"] == "cpu"
    assert "timeout" in kwargs
    assert kwargs["timeout"] == 12
    file_tuple = kwargs["files"]["file"]
    assert file_tuple[0] == audio_file.name
    assert file_tuple[2] == "audio/x-wav"


def test_transcribe_webui_accepts_preflattened_options(audio_file: Path):
    session = DummySession()
    options = {
        "whisper.model_size": "base",
        "custom": "value",
        "whisper": {"lang": None},
    }

    transcribe_webui(
        "http://localhost", str(audio_file), options=options, session=session
    )

    _, kwargs = session.calls[0]
    data = kwargs["data"]
    assert data["whisper.model_size"] == "base"
    assert data["custom"] == "value"
    assert "whisper.lang" not in data
