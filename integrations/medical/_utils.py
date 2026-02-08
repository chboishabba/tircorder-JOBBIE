from __future__ import annotations

import hashlib
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


_TS_PREFIX_ISO_Z_RE = re.compile(r"^(?P<ts>\d{4}-\d{2}-\d{2}T\d{6}Z)(?:[_-].*)?$")
_TS_PREFIX_DATE_DASH_RE = re.compile(r"^(?P<y>\d{4})-(?P<m>\d{2})-(?P<d>\d{2})(?:[_-].*)?$")
_TS_PREFIX_DATE_COMPACT_RE = re.compile(r"^(?P<y>\d{4})(?P<m>\d{2})(?P<d>\d{2})(?:[_-].*)?$")


def sha256_file(path: str | Path) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def parse_timestamp_from_filename(filename: str) -> Optional[datetime]:
    """Best-effort timestamp extraction from filename prefixes.

    Supported prefixes (UTC):
    - YYYY-MM-DDTHHMMSSZ_...
    - YYYY-MM-DD_...
    - YYYYMMDD_...
    """

    name = Path(filename).name

    m = _TS_PREFIX_ISO_Z_RE.match(name)
    if m:
        ts = m.group("ts")
        # YYYY-MM-DDTHHMMSSZ -> YYYY-MM-DDTHH:MM:SS+00:00
        dt = datetime.strptime(ts, "%Y-%m-%dT%H%M%SZ").replace(tzinfo=timezone.utc)
        return dt

    m = _TS_PREFIX_DATE_DASH_RE.match(name)
    if m:
        dt = datetime(
            int(m.group("y")),
            int(m.group("m")),
            int(m.group("d")),
            tzinfo=timezone.utc,
        )
        return dt

    m = _TS_PREFIX_DATE_COMPACT_RE.match(name)
    if m:
        dt = datetime(
            int(m.group("y")),
            int(m.group("m")),
            int(m.group("d")),
            tzinfo=timezone.utc,
        )
        return dt

    return None


def ensure_datetime(value: str, *, default_tz: timezone = timezone.utc) -> Optional[datetime]:
    """Parse common ISO 8601-ish FHIR timestamp strings into an aware datetime."""

    text = (value or "").strip()
    if not text:
        return None
    # FHIR often uses "Z".
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        dt = datetime.fromisoformat(text)
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=default_tz)
    return dt


def isoformat_utc(dt: datetime) -> str:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).isoformat()

