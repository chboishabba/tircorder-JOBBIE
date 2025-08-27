"""Parse LinkedIn data export files into story events."""

from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List
from uuid import uuid4

from tircorder.schemas import validate_story


class LinkedInBackupConnector:
    """Load timeline events from a LinkedIn data export directory."""

    def __init__(self, export_dir: str | Path) -> None:
        self.export_dir = Path(export_dir)

    def load_events(self) -> List[Dict]:
        """Return story events from the export directory."""

        events: List[Dict] = []
        events.extend(self._load_messages())
        events.extend(self._load_profile_updates())
        events.extend(self._load_posts())
        return events

    def _load_messages(self) -> List[Dict]:
        path = self.export_dir / "messages.csv"
        if not path.exists():
            return []
        events: List[Dict] = []
        with open(path, newline="", encoding="utf-8") as fh:
            reader = csv.DictReader(fh)
            for row in reader:
                ts = self._parse_ts(row.get("Date"))
                if not ts:
                    continue
                event = {
                    "event_id": f"linkedin_msg_{uuid4()}",
                    "timestamp": ts,
                    "actor": row.get("From") or "unknown",
                    "action": "message",
                    "details": {
                        "to": row.get("To"),
                        "text": row.get("Message", ""),
                    },
                }
                validate_story(event)
                events.append(event)
        return events

    def _load_profile_updates(self) -> List[Dict]:
        path = self.export_dir / "profile_updates.json"
        if not path.exists():
            return []
        with open(path, "r", encoding="utf-8") as fh:
            raw_items = json.load(fh)
        events: List[Dict] = []
        for item in raw_items:
            ts = self._parse_ts(item.get("timestamp"))
            if not ts:
                continue
            event = {
                "event_id": f"linkedin_profile_{uuid4()}",
                "timestamp": ts,
                "actor": "user",
                "action": "profile_update",
                "details": {
                    "update": item.get("update"),
                    "location": item.get("location"),
                },
            }
            validate_story(event)
            events.append(event)
        return events

    def _load_posts(self) -> List[Dict]:
        path = self.export_dir / "posts.json"
        if not path.exists():
            return []
        with open(path, "r", encoding="utf-8") as fh:
            raw_items = json.load(fh)
        events: List[Dict] = []
        for item in raw_items:
            ts = self._parse_ts(item.get("timestamp"))
            if not ts:
                continue
            event = {
                "event_id": f"linkedin_post_{uuid4()}",
                "timestamp": ts,
                "actor": "user",
                "action": "post",
                "details": {
                    "text": item.get("text"),
                    "url": item.get("url"),
                },
            }
            validate_story(event)
            events.append(event)
        return events

    @staticmethod
    def _parse_ts(ts: str | None) -> str | None:
        if not ts:
            return None
        cleaned = ts.strip().replace("Z", "+00:00")
        try:
            dt = datetime.fromisoformat(cleaned)
        except ValueError:
            dt = None
            for fmt in ("%Y-%m-%d %H:%M:%S %z", "%Y-%m-%dT%H:%M:%S%z"):
                try:
                    dt = datetime.strptime(cleaned, fmt)
                    break
                except ValueError:
                    continue
            if dt is None:
                return None
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        else:
            dt = dt.astimezone(timezone.utc)
        return dt.isoformat()
