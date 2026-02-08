"""Medical scan folder ingestion (metadata-only).

This connector walks a directory of scan artifacts (DICOM or exported image/PDF
files) and emits story events referencing each file by SHA-256.

No DICOM tag parsing is performed (no pydicom dependency).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence

from tircorder.schemas import validate_story

from ._utils import isoformat_utc, parse_timestamp_from_filename, sha256_file


_DEFAULT_EXTS = {".dcm", ".pdf", ".png", ".jpg", ".jpeg"}


def _scan_kind_for_ext(ext: str) -> str:
    e = (ext or "").lower()
    if e == ".dcm":
        return "dicom"
    if e == ".pdf":
        return "pdf"
    if e in {".png", ".jpg", ".jpeg"}:
        return "image"
    return "file"


@dataclass
class ScanFolderConnector:
    root: str | Path
    actor: str = "user"
    action: str = "medical_scan"
    exts: Sequence[str] = tuple(sorted(_DEFAULT_EXTS))
    recursive: bool = True
    include_relpath: bool = False

    def load(self, *, collected_at: Optional[datetime] = None) -> List[Dict[str, Any]]:
        base = Path(self.root)
        if collected_at is None:
            collected_at = datetime.now(timezone.utc)

        exts = {e.lower() if e.startswith(".") else f".{e.lower()}" for e in self.exts}

        files: Iterable[Path]
        if self.recursive:
            files = (p for p in base.rglob("*") if p.is_file())
        else:
            files = (p for p in base.glob("*") if p.is_file())

        events: List[Dict[str, Any]] = []
        for path in sorted(files):
            if path.suffix.lower() not in exts:
                continue
            digest = sha256_file(path)
            ts = parse_timestamp_from_filename(path.name) or collected_at
            details: Dict[str, Any] = {
                "sha256": digest,
                "file_size_bytes": path.stat().st_size,
                "filename": path.name,
                "ext": path.suffix.lower(),
                "scan_kind": _scan_kind_for_ext(path.suffix),
            }
            if self.include_relpath:
                details["relpath"] = str(path.relative_to(base))

            event = {
                "event_id": f"medical_scan_{digest[:12]}",
                "timestamp": isoformat_utc(ts),
                "actor": self.actor,
                "action": self.action,
                "details": details,
            }
            validate_story(event)
            events.append(event)

        return events


__all__ = ["ScanFolderConnector"]

