from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence


DEFAULT_SEGMENT_KEYS = ("text", "start", "end", "speaker", "confidence")
DEFAULT_BROWSER_PREVIEW_CHARS = 240


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def _sha256_json(payload: Mapping[str, Any]) -> str:
    blob = json.dumps(payload, sort_keys=True, ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _collapse_ws(value: Any) -> str:
    return " ".join(str(value or "").split())


def _truncate(value: Any, max_chars: int) -> str | None:
    text = _collapse_ws(value)
    if not text:
        return None
    limit = max(1, max_chars)
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "…"


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


def build_browser_assist_session(
    *,
    session_id: str,
    task_label: str,
    started_at: str,
    ended_at: str | None = None,
    browser: str | None = None,
    page_url: str | None = None,
    page_title: str | None = None,
    text_preview: str | None = None,
    openrecall_entry_refs: Sequence[str] | None = None,
    playwright_snapshot_refs: Sequence[str] | None = None,
    transcript_refs: Sequence[str] | None = None,
    pnf_candidates: Sequence[Mapping[str, Any]] | None = None,
    task_identity_residual: str | None = None,
    lifecycle_residual: str | None = None,
    kanban_projection_policy: str = "observer_only",
    storage_mode: str = "preview_plus_hashes",
    preview_chars: int = DEFAULT_BROWSER_PREVIEW_CHARS,
    adapter_label: str = "tircorder_browser_assist_v1",
) -> dict[str, Any]:
    """Build a non-authoritative browser-assist capture session artifact."""

    clean_preview = _truncate(text_preview, preview_chars)
    artifact = {
        "version": "browser_assist_session_v1",
        "session_id": session_id,
        "task_label": task_label,
        "started_at": started_at,
        "ended_at": ended_at,
        "browser": browser,
        "page_url_hash": f"sha256:{_sha256_text(page_url)}" if page_url else None,
        "page_title_hash": f"sha256:{_sha256_text(page_title)}" if page_title else None,
        "text_preview": clean_preview if storage_mode != "metadata_only" else None,
        "text_hash": f"sha256:{_sha256_text(text_preview)}" if text_preview else None,
        "openrecall_entry_refs": list(openrecall_entry_refs or []),
        "playwright_snapshot_refs": list(playwright_snapshot_refs or []),
        "transcript_refs": list(transcript_refs or []),
        "pnf_candidates": [dict(item) for item in (pnf_candidates or []) if isinstance(item, Mapping)],
        "task_identity_residual": task_identity_residual,
        "lifecycle_residual": lifecycle_residual,
        "kanban_projection_policy": kanban_projection_policy,
        "storage_mode": storage_mode,
        "non_authoritative": True,
        "provenance": {
            "adapter": adapter_label,
            "created_at": datetime.now(timezone.utc).isoformat(),
        },
    }
    artifact["artifact_hash"] = f"sha256:{_sha256_json(artifact)}"
    return artifact


__all__ = [
    "build_browser_assist_session",
    "build_execution_envelope",
    "write_execution_envelope",
    "DEFAULT_SEGMENT_KEYS",
]
