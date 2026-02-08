"""Doctor notes folder ingestion.

This connector emits story events for note artifacts in a directory.

Default posture is meta-only: it records hashes and file metadata.
Optionally, callers may include plaintext content for .txt/.md files.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence

from tircorder.schemas import validate_story

from ._utils import isoformat_utc, parse_timestamp_from_filename, sha256_file


_DEFAULT_EXTS = {".txt", ".md", ".pdf"}


@dataclass
class DoctorNotesFolderConnector:
    root: str | Path
    actor: str = "user"
    action: str = "doctor_note"
    exts: Sequence[str] = tuple(sorted(_DEFAULT_EXTS))
    recursive: bool = True
    include_text: bool = False
    max_text_bytes: int = 200_000
    include_relpath: bool = False
    doc_kind: str = "doctor_note"

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
                "doc_kind": self.doc_kind,
            }
            if self.include_relpath:
                details["relpath"] = str(path.relative_to(base))

            if self.include_text and path.suffix.lower() in {".txt", ".md"}:
                # Avoid pulling huge exports into the story event stream.
                raw = path.read_bytes()
                if len(raw) > self.max_text_bytes:
                    details["text_truncated"] = True
                    raw = raw[: self.max_text_bytes]
                details["text"] = raw.decode("utf-8", errors="replace")

            event = {
                "event_id": f"doctor_note_{digest[:12]}",
                "timestamp": isoformat_utc(ts),
                "actor": self.actor,
                "action": self.action,
                "details": details,
            }
            validate_story(event)
            events.append(event)

        return events


__all__ = ["DoctorNotesFolderConnector"]

