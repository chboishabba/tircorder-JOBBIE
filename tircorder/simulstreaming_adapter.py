from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence


SIMULSTREAMING_SOURCE = "simulstreaming_jsonl"


def load_simulstreaming_jsonl(path: str | Path) -> list[dict[str, Any]]:
    """Load SimulStreaming JSONL output into validated event objects."""

    source = Path(path)
    return parse_simulstreaming_jsonl(source.read_text(encoding="utf-8"))


def parse_simulstreaming_jsonl(text: str) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    for line_no, raw_line in enumerate(text.splitlines(), start=1):
        line = raw_line.strip()
        if not line:
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid SimulStreaming JSONL at line {line_no}") from exc
        if not isinstance(payload, dict):
            raise ValueError(f"SimulStreaming JSONL line {line_no} must be an object")
        events.append(payload)
    return events


def normalize_simulstreaming_events(
    events: Sequence[Mapping[str, Any]],
    *,
    model: str | None = None,
    language: str | None = None,
    source: str = SIMULSTREAMING_SOURCE,
    include_unconfirmed_final: bool = False,
) -> dict[str, Any]:
    """Convert SimulStreaming incremental JSONL rows into Tircorder transcript payload."""

    confirmed_text = ""
    segments: list[dict[str, Any]] = []
    partial_updates: list[dict[str, Any]] = []
    last_segment_end = 0.0
    last_unconfirmed = ""

    for sequence, event in enumerate(events, start=1):
        row_text = _clean_text(event.get("text"))
        unconfirmed_text = _clean_text(event.get("unconfirmed_text"))
        if unconfirmed_text:
            last_unconfirmed = unconfirmed_text
        end = _optional_float(event.get("end"))
        emission_time = _optional_float(event.get("emission_time"))
        status = str(event.get("status") or "").strip() or None
        is_final = bool(event.get("is_final")) if "is_final" in event else None

        partial_updates.append(
            {
                "sequence": sequence,
                "text": row_text,
                "unconfirmed_text": unconfirmed_text,
                "status": status,
                "is_final": is_final,
                "end": end,
                "emission_time": emission_time,
            }
        )

        delta = _confirmed_delta(confirmed_text, row_text)
        if not delta:
            continue

        segment_start = last_segment_end
        segment_end = end if end is not None else segment_start
        if segment_end < segment_start:
            segment_start = segment_end
        segments.append(
            {
                "text": delta,
                "start": segment_start,
                "end": segment_end,
                "source": source,
                "status": status,
                "emission_time": emission_time,
                "is_final": is_final,
            }
        )
        confirmed_text = _merge_confirmed_text(confirmed_text, row_text)
        last_segment_end = segment_end

    if not confirmed_text and include_unconfirmed_final and last_unconfirmed:
        confirmed_text = last_unconfirmed
        segments.append(
            {
                "text": last_unconfirmed,
                "start": 0.0,
                "end": _last_end(events) or 0.0,
                "source": source,
                "status": "UNCONFIRMED_FINAL",
                "emission_time": None,
                "is_final": False,
            }
        )

    return {
        "text": confirmed_text.strip(),
        "model": model,
        "language": language,
        "segments": segments,
        "source": source,
        "partial_updates": partial_updates,
    }


def normalize_simulstreaming_jsonl(
    text: str,
    *,
    model: str | None = None,
    language: str | None = None,
    source: str = SIMULSTREAMING_SOURCE,
    include_unconfirmed_final: bool = False,
) -> dict[str, Any]:
    return normalize_simulstreaming_events(
        parse_simulstreaming_jsonl(text),
        model=model,
        language=language,
        source=source,
        include_unconfirmed_final=include_unconfirmed_final,
    )


def normalize_simulstreaming_jsonl_file(
    path: str | Path,
    *,
    model: str | None = None,
    language: str | None = None,
    source: str = SIMULSTREAMING_SOURCE,
    include_unconfirmed_final: bool = False,
) -> dict[str, Any]:
    return normalize_simulstreaming_events(
        load_simulstreaming_jsonl(path),
        model=model,
        language=language,
        source=source,
        include_unconfirmed_final=include_unconfirmed_final,
    )


def _clean_text(value: Any) -> str:
    if value is None:
        return ""
    return " ".join(str(value).split())


def _optional_float(value: Any) -> float | None:
    if isinstance(value, (int, float)):
        return float(value)
    return None


def _confirmed_delta(previous: str, current: str) -> str:
    previous = previous.strip()
    current = current.strip()
    if not current or current == previous:
        return ""
    if previous and current.startswith(previous):
        return current[len(previous) :].strip()
    return current


def _merge_confirmed_text(previous: str, current: str) -> str:
    previous = previous.strip()
    current = current.strip()
    if not previous:
        return current
    if current.startswith(previous):
        return current
    if current == previous:
        return previous
    return f"{previous} {current}".strip()


def _last_end(events: Iterable[Mapping[str, Any]]) -> float | None:
    last: float | None = None
    for event in events:
        value = _optional_float(event.get("end"))
        if value is not None:
            last = value
    return last

