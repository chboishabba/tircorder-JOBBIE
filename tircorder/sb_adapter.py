from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence


DEFAULT_SEGMENT_KEYS = ("text", "start", "end", "speaker", "confidence")


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def _sha256_json(payload: Mapping[str, Any]) -> str:
    blob = json.dumps(payload, sort_keys=True, ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


def build_execution_envelope(
    transcript: Mapping[str, Any],
    *,
    source: str = "whisperx_webui",
    model: str | None = None,
    language: str | None = None,
    audio_path: str | Path | None = None,
    segment_keys: Sequence[str] = DEFAULT_SEGMENT_KEYS,
    adapter_label: str = "tircorder_whisperx_webui_v1",
    envelope_format: str = "sb_execution_envelope_v1",
) -> dict:
    """Build a SB-ready execution envelope + segment events from ASR output.

    This is a non-semantic adapter: it preserves provided values and never
    injects interpretive labels.
    """

    audio_hash = _sha256_file(Path(audio_path)) if audio_path else None
    segments = transcript.get("segments", []) or []
    transcript_hash = _sha256_json(transcript)

    envelope_id_source = f"{source}:{transcript_hash}:{audio_hash or 'no-audio'}"
    envelope_id = hashlib.sha256(envelope_id_source.encode("utf-8")).hexdigest()

    envelope = {
        "type": "execution_envelope",
        "id": envelope_id,
        "format": envelope_format,
        "source": source,
        "toolchain": {
            "model": model or transcript.get("model"),
            "language": language or transcript.get("language"),
        },
        "audio_hash": audio_hash,
        "segment_count": len(segments),
        "provenance": {
            "transcript_hash": transcript_hash,
            "adapter": adapter_label,
        },
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    allowed = set(segment_keys)
    segment_events = []
    for seg in segments:
        if not isinstance(seg, Mapping):
            continue
        data = {k: seg.get(k) for k in allowed if k in seg}
        data["provenance"] = {"source": source, "envelope_id": envelope_id}
        if audio_hash:
            data["audio_hash"] = audio_hash
        segment_events.append({"type": "audio_segment", "data": data})

    return {
        "execution_envelope": envelope,
        "segment_events": segment_events,
    }


def write_execution_envelope(path: str | Path, payload: Mapping[str, Any]) -> Path:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return target


__all__ = ["build_execution_envelope", "write_execution_envelope", "DEFAULT_SEGMENT_KEYS"]
