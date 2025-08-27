"""Parse Facebook data download directories."""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterator, List


class FacebookBackupConnector:
    """Connector for Facebook "Download Your Information" archives.

    The connector expects the root of an extracted Facebook data export. The
    following directory layout is used::

        archive/
            posts/your_posts.json
            messages/inbox/<thread>/message_1.json
            reactions/reactions.json
            media/...

    Methods yielding events return dictionaries with the standard story
    fields ``event_id``, ``timestamp``, ``actor``, ``action`` and ``details``.
    """

    def __init__(self, root: str) -> None:
        self.root = Path(root)

    def _make_event(
        self, dt: datetime, actor: str, action: str, details: Dict[str, Any]
    ) -> Dict[str, Any]:
        event = {
            "event_id": str(uuid.uuid4()),
            "timestamp": dt.replace(tzinfo=timezone.utc).isoformat(),
            "actor": actor,
            "action": action,
            "details": details,
        }
        self._validate_event(event)
        return event

    @staticmethod
    def _validate_event(event: Dict[str, Any]) -> None:
        """Ensure *event* contains the required story keys."""

        required = {"event_id", "timestamp", "actor", "action", "details"}
        missing = required - set(event)
        if missing:
            raise ValueError(f"Missing keys in event: {sorted(missing)}")

    def iter_posts(self) -> Iterator[Dict[str, Any]]:
        """Yield events for each post in ``posts/your_posts.json``."""

        path = self.root / "posts" / "your_posts.json"
        if not path.exists():
            return
        with open(path, "r", encoding="utf-8") as fh:
            raw = json.load(fh)
        for item in raw.get("posts", []):
            ts = item.get("timestamp")
            if ts is None:
                continue
            dt = datetime.fromtimestamp(ts, tz=timezone.utc)
            text = ""
            for data in item.get("data", []):
                text = data.get("post") or text
            media: List[str] = []
            for att in item.get("attachments", []):
                for data in att.get("data", []):
                    uri = data.get("media", {}).get("uri")
                    if uri:
                        media.append(str(self.root / uri))
            details: Dict[str, Any] = {"text": text}
            if media:
                details["media"] = media
            yield self._make_event(dt, "me", "post", details)

    def iter_messages(self) -> Iterator[Dict[str, Any]]:
        """Yield events for each message in ``messages/inbox``."""

        inbox = self.root / "messages" / "inbox"
        if not inbox.exists():
            return
        for path in inbox.glob("*/message_*.json"):
            with open(path, "r", encoding="utf-8") as fh:
                raw = json.load(fh)
            thread = path.parent.name
            for msg in raw.get("messages", []):
                ts_ms = msg.get("timestamp_ms")
                if ts_ms is None:
                    continue
                dt = datetime.fromtimestamp(ts_ms / 1000, tz=timezone.utc)
                actor = msg.get("sender_name", "unknown")
                text = msg.get("content", "")
                media: List[str] = []
                for photo in msg.get("photos", []):
                    uri = photo.get("uri")
                    if uri:
                        media.append(str(self.root / uri))
                details: Dict[str, Any] = {"text": text, "thread": thread}
                if media:
                    details["media"] = media
                yield self._make_event(dt, actor, "message", details)

    def iter_reactions(self) -> Iterator[Dict[str, Any]]:
        """Yield events for each reaction in ``reactions/reactions.json``."""

        path = self.root / "reactions" / "reactions.json"
        if not path.exists():
            return
        with open(path, "r", encoding="utf-8") as fh:
            raw = json.load(fh)
        for item in raw.get("reactions", []):
            ts = item.get("timestamp")
            if ts is None:
                continue
            dt = datetime.fromtimestamp(ts, tz=timezone.utc)
            details: Dict[str, Any] = {
                "title": item.get("title"),
                "url": item.get("uri"),
            }
            yield self._make_event(dt, "me", "reaction", details)

    def iter_events(self) -> Iterator[Dict[str, Any]]:
        """Yield all parsed events in chronological order."""

        yield from self.iter_posts()
        yield from self.iter_messages()
        yield from self.iter_reactions()


__all__ = ["FacebookBackupConnector"]
