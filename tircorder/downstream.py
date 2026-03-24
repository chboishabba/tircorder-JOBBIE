from __future__ import annotations

import hashlib
import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict, Mapping, Optional


_SUITE_ROOT = Path(__file__).resolve().parents[2]
_SENSIBLAW_ROOT = _SUITE_ROOT / "SensibLaw"
_SENSIBLAW_SRC = _SENSIBLAW_ROOT / "src"
_STATIBAKER_ROOT = _SUITE_ROOT / "StatiBaker"

for candidate in (_SENSIBLAW_ROOT, _SENSIBLAW_SRC, _STATIBAKER_ROOT):
    if candidate.exists() and str(candidate) not in sys.path:
        sys.path.insert(0, str(candidate))


def write_json_artifact(path: str | Path, payload: Mapping[str, Any]) -> Path:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return target


def write_downstream_receipts(path: str | Path, payload: Mapping[str, Any]) -> Path:
    return write_json_artifact(path, payload)


def build_downstream_receipts(
    *,
    metadata: Mapping[str, Any],
    transcript_payload: Mapping[str, Any],
    transcript_artifact_path: Optional[str | Path] = None,
) -> Dict[str, Any]:
    transcript_hash = hashlib.sha256(
        json.dumps(transcript_payload, sort_keys=True, ensure_ascii=False).encode("utf-8")
    ).hexdigest()
    return {
        "job_id": metadata.get("task_id"),
        "protocol": metadata.get("protocol"),
        "completed_at": metadata.get("completed_at"),
        "transcript_hash": transcript_hash,
        "transcript_artifact_path": str(transcript_artifact_path) if transcript_artifact_path else None,
        "sinks": {},
    }


def ingest_into_sensiblaw(
    transcript_payload: Mapping[str, Any],
    *,
    audio_path: str | Path,
    storage_path: str | Path,
) -> Dict[str, Any]:
    from sensiblaw.ingest.whisperx_adapter import import_whisperx_transcript
    from storage.core import Storage

    store = Storage(storage_path)
    try:
        envelope_id = import_whisperx_transcript(
            store,
            transcript_payload,
            audio_path=audio_path,
        )
        return {
            "status": "ok",
            "storage_path": str(storage_path),
            "envelope_id": envelope_id,
        }
    finally:
        store.close()


def append_into_statibaker(
    execution_envelope: Mapping[str, Any],
    *,
    log_root: str | Path,
    transcript_artifact_path: Optional[str | Path] = None,
    completed_at: Optional[str] = None,
) -> Dict[str, Any]:
    from adapters.whisperx_webui_execution import append_transcription_activity_log

    return append_transcription_activity_log(
        log_root=log_root,
        execution_envelope=execution_envelope,
        transcript_artifact_path=transcript_artifact_path,
        completed_at=completed_at,
    )


def fanout_whisperx_downstream(
    *,
    audio_path: str | Path,
    transcript_payload: Mapping[str, Any],
    execution_envelope: Optional[Mapping[str, Any]],
    metadata: Mapping[str, Any],
    downstream_config: Mapping[str, Any],
    transcript_artifact_path: Optional[str | Path] = None,
) -> Dict[str, Any]:
    receipts = build_downstream_receipts(
        metadata=metadata,
        transcript_payload=transcript_payload,
        transcript_artifact_path=transcript_artifact_path,
    )

    sensiblaw_config = dict(downstream_config.get("sensiblaw") or {})
    if sensiblaw_config.get("enabled") and sensiblaw_config.get("storage_path"):
        try:
            receipts["sinks"]["sensiblaw"] = ingest_into_sensiblaw(
                transcript_payload,
                audio_path=audio_path,
                storage_path=sensiblaw_config["storage_path"],
            )
        except Exception as exc:  # pragma: no cover - sink failure path
            logging.error("SensibLaw ingest failed: %s", exc)
            receipts["sinks"]["sensiblaw"] = {
                "status": "error",
                "error": str(exc),
                "storage_path": sensiblaw_config.get("storage_path"),
            }

    statibaker_config = dict(downstream_config.get("statibaker") or {})
    if (
        execution_envelope
        and statibaker_config.get("enabled")
        and statibaker_config.get("log_root")
    ):
        try:
            receipts["sinks"]["statibaker"] = append_into_statibaker(
                execution_envelope,
                log_root=statibaker_config["log_root"],
                transcript_artifact_path=transcript_artifact_path,
                completed_at=metadata.get("completed_at"),
            )
        except Exception as exc:  # pragma: no cover - sink failure path
            logging.error("StatiBaker ingest failed: %s", exc)
            receipts["sinks"]["statibaker"] = {
                "status": "error",
                "error": str(exc),
                "log_root": statibaker_config.get("log_root"),
            }

    return receipts

