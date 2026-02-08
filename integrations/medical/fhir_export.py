"""FHIR export ingestion (meta-only by default).

This connector ingests user-provided FHIR exports (Bundle JSON, NDJSON, or a
directory of JSON files) and emits TiRCorder story events.

Guardrails:
- meta-only by default (no base64 attachments, no free-text narrative)
- hashed identifiers (avoid leaking raw IDs into story events)
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, Iterator, List, Mapping, Optional

from tircorder.schemas import validate_story

from ._utils import ensure_datetime, isoformat_utc, sha256_text


_FHIR_TIME_KEYS = (
    ("meta", "lastUpdated"),
    ("issued",),
    ("effectiveDateTime",),
    ("date",),
    ("created",),
)


def _get_nested(resource: Mapping[str, Any], path: tuple[str, ...]) -> Optional[Any]:
    cur: Any = resource
    for key in path:
        if not isinstance(cur, Mapping):
            return None
        cur = cur.get(key)
    return cur


def _iter_bundle_entries(payload: Any) -> Iterator[Mapping[str, Any]]:
    if isinstance(payload, Mapping) and payload.get("resourceType") == "Bundle":
        for entry in payload.get("entry", []) or []:
            res = entry.get("resource") if isinstance(entry, Mapping) else None
            if isinstance(res, Mapping):
                yield res
        return
    if isinstance(payload, list):
        for item in payload:
            if isinstance(item, Mapping):
                yield item
        return
    if isinstance(payload, Mapping):
        yield payload


def _iter_resources_from_file(path: Path) -> Iterator[Mapping[str, Any]]:
    if path.suffix.lower() == ".ndjson":
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            obj = json.loads(line)
            if isinstance(obj, Mapping):
                yield obj
        return
    payload = json.loads(path.read_text(encoding="utf-8"))
    yield from _iter_bundle_entries(payload)


def _iter_resources(path: Path) -> Iterator[Mapping[str, Any]]:
    if path.is_dir():
        files = sorted([p for p in path.rglob("*") if p.is_file() and p.suffix.lower() in {".json", ".ndjson"}])
        for f in files:
            yield from _iter_resources_from_file(f)
        return
    yield from _iter_resources_from_file(path)


def _resource_timestamp(resource: Mapping[str, Any]) -> Optional[datetime]:
    for key_path in _FHIR_TIME_KEYS:
        raw = _get_nested(resource, key_path)
        if isinstance(raw, str):
            dt = ensure_datetime(raw)
            if dt is not None:
                return dt
    # Some resources use effectivePeriod.start
    effective_period = resource.get("effectivePeriod")
    if isinstance(effective_period, Mapping):
        start = effective_period.get("start")
        if isinstance(start, str):
            dt = ensure_datetime(start)
            if dt is not None:
                return dt
    # Date-only fields appear in a few places; accept them as midnight UTC.
    for key in ("birthDate", "recordedDate"):
        raw = resource.get(key)
        if isinstance(raw, str) and len(raw) == 10 and raw[4] == "-" and raw[7] == "-":
            try:
                dt = datetime.fromisoformat(raw).replace(tzinfo=timezone.utc)
                return dt
            except ValueError:
                pass
    return None


def _safe_code_list(obj: Any) -> list[dict]:
    """Extract minimal coding tuples from a CodeableConcept-like object."""

    if not isinstance(obj, Mapping):
        return []
    coding = obj.get("coding")
    if not isinstance(coding, list):
        return []
    out: list[dict] = []
    for item in coding:
        if not isinstance(item, Mapping):
            continue
        system = item.get("system")
        code = item.get("code")
        if not system and not code:
            continue
        out.append({"system": system, "code": code})
    return out


def _sanitize_resource(resource: Mapping[str, Any]) -> dict:
    """Return meta-only fields for the story event details payload."""

    resource_type = str(resource.get("resourceType") or "Unknown")
    status = resource.get("status")

    details: dict = {
        "resource_type": resource_type,
    }
    if isinstance(status, str):
        details["status"] = status

    # Minimal codes for common fields (avoid display strings).
    for field in ("type", "code", "category"):
        codes = _safe_code_list(resource.get(field))
        if codes:
            details[f"{field}_codes"] = codes

    # DocumentReference attachment metadata (never attachment.data).
    if resource_type == "DocumentReference":
        content = resource.get("content")
        if isinstance(content, list):
            refs: list[dict] = []
            for item in content:
                if not isinstance(item, Mapping):
                    continue
                att = item.get("attachment")
                if not isinstance(att, Mapping):
                    continue
                refs.append(
                    {
                        "content_type": att.get("contentType"),
                        "title": att.get("title"),
                        "has_data": bool(att.get("data")),
                        "url_present": bool(att.get("url")),
                        "size": att.get("size"),
                    }
                )
            if refs:
                details["attachment_refs"] = refs

    return details


@dataclass
class FHIRExportConnector:
    """Parse local FHIR exports into meta-only story events."""

    actor: str = "ehr"
    action: str = "fhir_resource"
    hash_salt: str = ""

    def load(self, path: str | Path, *, collected_at: Optional[datetime] = None) -> List[Dict[str, Any]]:
        root = Path(path)
        if collected_at is None:
            collected_at = datetime.now(timezone.utc)

        events: List[Dict[str, Any]] = []
        for resource in _iter_resources(root):
            resource_type = str(resource.get("resourceType") or "Unknown")
            rid = resource.get("id")
            id_material = f"{self.hash_salt}|{resource_type}:{rid}" if rid else f"{self.hash_salt}|{resource_type}:{json.dumps(resource, sort_keys=True)}"
            resource_id_hash = sha256_text(id_material)

            ts = _resource_timestamp(resource) or collected_at
            details = _sanitize_resource(resource)
            details["resource_id_hash"] = resource_id_hash

            event = {
                "event_id": f"fhir_{resource_type.lower()}_{resource_id_hash[:12]}",
                "timestamp": isoformat_utc(ts),
                "actor": self.actor,
                "action": self.action,
                "details": details,
            }
            validate_story(event)
            events.append(event)
        return events


__all__ = ["FHIRExportConnector"]

