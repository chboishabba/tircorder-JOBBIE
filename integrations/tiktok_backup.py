"""Connector for TikTok data export archives."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable, Iterator, List
from uuid import uuid4

from tircorder.schemas import validate_story


class TikTokBackupConnector:
    """Parse TikTok data downloads into story events."""

    def __init__(self, directory: str | Path) -> None:
        self.directory = Path(directory)

    def _load_file(self, candidates: Iterable[str]) -> List[Dict]:
        """Return the first list found among *candidates*.

        TikTok exports sometimes wrap lists in a top-level object. This helper
        attempts to locate the relevant list regardless of the exact structure.
        """

        for name in candidates:
            path = self.directory / name
            if not path.exists():
                continue
            with open(path, "r", encoding="utf-8") as fh:
                data = json.load(fh)
            if isinstance(data, list):
                return data
            if isinstance(data, dict):
                for value in data.values():
                    if isinstance(value, list):
                        return value
        return []

    def iter_video_history(self) -> Iterator[Dict]:
        """Yield watch events from the user's video history."""

        entries = self._load_file(["Video Browsing History.json", "videos.json"])
        for item in entries:
            date_str = item.get("Date") or item.get("date")
            if not date_str:
                continue
            try:
                dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
            except ValueError:
                continue
            details = {
                k: v
                for k, v in {
                    "title": item.get("Title") or item.get("title"),
                    "link": item.get("Link") or item.get("url"),
                }.items()
                if v
            }
            event = {
                "event_id": f"tiktok_video_{uuid4()}",
                "timestamp": dt.isoformat(),
                "actor": "user",
                "action": "watch",
                "details": details,
            }
            validate_story(event)
            yield event

    def iter_comments(self) -> Iterator[Dict]:
        """Yield comment events from the user's history."""

        entries = self._load_file(["Comments.json", "comments.json"])
        for item in entries:
            date_str = item.get("Date") or item.get("date")
            if not date_str:
                continue
            try:
                dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
            except ValueError:
                continue
            actor = item.get("From") or item.get("from") or "user"
            details = {
                k: v
                for k, v in {
                    "text": item.get("Comment") or item.get("text"),
                    "link": item.get("Link") or item.get("url"),
                    "to": item.get("To") or item.get("to"),
                }.items()
                if v
            }
            event = {
                "event_id": f"tiktok_comment_{uuid4()}",
                "timestamp": dt.isoformat(),
                "actor": actor,
                "action": "comment",
                "details": details,
            }
            validate_story(event)
            yield event

    def iter_messages(self) -> Iterator[Dict]:
        """Yield direct message events."""

        entries = self._load_file(["Messages.json", "messages.json"])
        for convo in entries:
            messages = convo.get("messages") if isinstance(convo, dict) else None
            if messages is None:
                messages = [convo]
            for item in messages:
                date_str = item.get("Date") or item.get("date")
                if not date_str:
                    continue
                try:
                    dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                except ValueError:
                    continue
                actor = item.get("From") or item.get("from") or "user"
                details = {
                    k: v
                    for k, v in {
                        "text": item.get("Content")
                        or item.get("text")
                        or item.get("Message"),
                        "to": item.get("To") or item.get("to"),
                    }.items()
                    if v
                }
                event = {
                    "event_id": f"tiktok_message_{uuid4()}",
                    "timestamp": dt.isoformat(),
                    "actor": actor,
                    "action": "message",
                    "details": details,
                }
                validate_story(event)
                yield event

    def iter_events(self) -> Iterator[Dict]:
        """Yield all events present in the backup directory."""

        yield from self.iter_video_history()
        yield from self.iter_comments()
        yield from self.iter_messages()
