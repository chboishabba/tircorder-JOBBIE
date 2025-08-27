"""Utilities for parsing Google Takeout archives."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Dict, Iterator
from uuid import uuid4
import json

from tircorder.schemas import validate_story


class GoogleTakeoutConnector:
    """Parse selected Google Takeout JSON exports into story events.

    Parameters
    ----------
    base_path:
        Root directory of the extracted Takeout archive.
    """

    def __init__(self, base_path: str | Path) -> None:
        self.base_path = Path(base_path)

    def iter_events(self) -> Iterator[Dict]:
        """Yield events parsed from supported Takeout files."""

        yield from self._parse_gmail_all_mail()
        yield from self._parse_drive_activity()
        yield from self._parse_photos_metadata()

    # Internal helpers -------------------------------------------------
    def _load_json_items(self, path: Path) -> Iterator[Dict]:
        """Yield JSON objects from ``path``.

        Supports newline-delimited JSON or arrays.  Malformed lines are skipped.
        """

        try:
            with open(path, "r", encoding="utf-8") as fh:
                start = fh.read(1)
                fh.seek(0)
                if start == "[":
                    try:
                        data = json.load(fh)
                    except json.JSONDecodeError:
                        return
                    for item in data:
                        if isinstance(item, dict):
                            yield item
                else:
                    for line in fh:
                        line = line.strip()
                        if not line:
                            continue
                        try:
                            item = json.loads(line)
                        except json.JSONDecodeError:
                            continue
                        if isinstance(item, dict):
                            yield item
        except OSError:
            return

    def _parse_gmail_all_mail(self) -> Iterator[Dict]:
        path = self.base_path / "Gmail" / "All mail.json"
        for item in self._load_json_items(path):
            ts = item.get("timestamp") or item.get("internalDate")
            if not ts:
                continue
            try:
                dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
            except ValueError:
                continue
            event = {
                "event_id": f"gmail_{item.get('id', uuid4())}",
                "timestamp": dt.isoformat(),
                "actor": item.get("from", "unknown"),
                "action": "email",
                "details": {
                    "subject": item.get("subject"),
                    "snippet": item.get("snippet"),
                },
            }
            try:
                validate_story(event)
            except Exception:
                continue
            yield event

    def _parse_drive_activity(self) -> Iterator[Dict]:
        path = self.base_path / "Drive" / "Activity.json"
        for item in self._load_json_items(path):
            ts = item.get("time") or item.get("timestamp")
            if not ts:
                continue
            try:
                dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
            except ValueError:
                continue
            event = {
                "event_id": f"drive_{uuid4()}",
                "timestamp": dt.isoformat(),
                "actor": item.get("actor", "user"),
                "action": item.get("action", "activity"),
                "details": {"target": item.get("target")},
            }
            try:
                validate_story(event)
            except Exception:
                continue
            yield event

    def _parse_photos_metadata(self) -> Iterator[Dict]:
        path = self.base_path / "Google Photos" / "metadata.json"
        for item in self._load_json_items(path):
            ts = item.get("creationTime") or item.get("timestamp")
            if not ts:
                continue
            try:
                dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
            except ValueError:
                continue
            event = {
                "event_id": f"photo_{uuid4()}",
                "timestamp": dt.isoformat(),
                "actor": "user",
                "action": "photo",
                "details": {"file_name": item.get("fileName")},
            }
            try:
                validate_story(event)
            except Exception:
                continue
            yield event
