from __future__ import annotations

import json
from pathlib import Path

from tircorder.downstream import (
    fanout_whisperx_downstream,
    write_downstream_receipts,
    write_json_artifact,
)


def test_write_json_artifact_round_trips(tmp_path):
    target = tmp_path / "nested" / "sample.json"
    written = write_json_artifact(target, {"text": "hello", "segments": []})

    assert written == target
    assert json.loads(target.read_text(encoding="utf-8"))["text"] == "hello"


def test_fanout_whisperx_downstream_collects_sink_receipts(monkeypatch, tmp_path):
    transcript_path = tmp_path / "sample.whisperx_transcript.json"
    transcript_path.write_text("{}", encoding="utf-8")

    monkeypatch.setattr(
        "tircorder.downstream.ingest_into_sensiblaw",
        lambda *_args, **_kwargs: {"status": "ok", "envelope_id": 42},
    )
    monkeypatch.setattr(
        "tircorder.downstream.append_into_statibaker",
        lambda *_args, **_kwargs: {"status": "appended", "event_id": "abc123"},
    )

    receipts = fanout_whisperx_downstream(
        audio_path=tmp_path / "audio.wav",
        transcript_payload={"text": "hello", "segments": []},
        execution_envelope={"id": "env-1", "segment_count": 0},
        metadata={"task_id": "task-1", "protocol": "backend", "completed_at": "2026-03-24T00:00:00Z"},
        downstream_config={
            "sensiblaw": {"enabled": True, "storage_path": str(tmp_path / "sl.db")},
            "statibaker": {"enabled": True, "log_root": str(tmp_path / "sb")},
        },
        transcript_artifact_path=transcript_path,
    )

    assert receipts["job_id"] == "task-1"
    assert receipts["protocol"] == "backend"
    assert receipts["sinks"]["sensiblaw"]["envelope_id"] == 42
    assert receipts["sinks"]["statibaker"]["event_id"] == "abc123"


def test_write_downstream_receipts_round_trips(tmp_path):
    target = tmp_path / "receipts.json"
    payload = {"job_id": "task-1", "sinks": {"sensiblaw": {"status": "ok"}}}
    write_downstream_receipts(target, payload)

    assert json.loads(target.read_text(encoding="utf-8")) == payload
