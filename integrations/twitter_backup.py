"""Parse Twitter data download archives."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List

from tircorder.schemas import validate_story


class TwitterBackupConnector:
    """Convert Twitter data export files into story events.

    Twitter's self-service data download returns JavaScript files such as
    ``tweet.js`` and ``like.js`` where the JSON payload is assigned to a global
    variable.  Direct message archives are similarly wrapped and may be split
    across multiple files.

    This connector extracts the JSON arrays from those files and converts each
    record into a standard story event validated against
    :func:`tircorder.schemas.validate_story`.
    """

    def _load_js(self, path: str) -> List[Dict]:
        """Load a JavaScript data file into a Python object."""
        text = Path(path).read_text(encoding="utf-8")
        start = text.find("[")
        end = text.rfind("]")
        if start == -1 or end == -1:
            return []
        return json.loads(text[start : end + 1])

    def _parse_time(self, value: str) -> str:
        """Normalise timestamp strings to ISO 8601."""
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00")).isoformat()
        except ValueError:
            dt = datetime.strptime(value, "%a %b %d %H:%M:%S %z %Y")
            return dt.isoformat()

    def parse_tweets(self, path: str) -> List[Dict]:
        """Parse ``tweet.js`` into story events."""
        records = self._load_js(path)
        events: List[Dict] = []
        for item in records:
            tweet = item.get("tweet", {})
            tweet_id = tweet.get("id") or tweet.get("id_str")
            created_at = tweet.get("created_at") or tweet.get("createdAt")
            text = tweet.get("full_text") or tweet.get("fullText") or tweet.get("text")
            if not tweet_id or not created_at:
                continue
            event = {
                "event_id": f"tweet_{tweet_id}",
                "timestamp": self._parse_time(created_at),
                "actor": "user",
                "action": "tweet",
                "details": {"id": tweet_id, "text": text},
            }
            validate_story(event)
            events.append(event)
        return events

    def parse_likes(self, path: str) -> List[Dict]:
        """Parse ``like.js`` into story events."""
        records = self._load_js(path)
        events: List[Dict] = []
        for item in records:
            like = item.get("like", {})
            tweet_id = like.get("tweetId")
            created_at = like.get("createdAt")
            text = like.get("fullText")
            url = like.get("expandedUrl")
            if not tweet_id or not created_at:
                continue
            event = {
                "event_id": f"like_{tweet_id}",
                "timestamp": self._parse_time(created_at),
                "actor": "user",
                "action": "like",
                "details": {"tweet_id": tweet_id, "text": text, "url": url},
            }
            validate_story(event)
            events.append(event)
        return events

    def parse_messages(self, path: str) -> List[Dict]:
        """Parse direct message archives into story events."""
        records = self._load_js(path)
        events: List[Dict] = []
        for conv in records:
            dm_conv = conv.get("dmConversation", {})
            conv_id = dm_conv.get("conversationId")
            for msg in dm_conv.get("messages", []):
                m = msg.get("messageCreate", {})
                msg_id = m.get("id")
                created_at = m.get("createdAt")
                sender = m.get("senderId")
                text = m.get("text")
                if not msg_id or not created_at:
                    continue
                event = {
                    "event_id": f"dm_{msg_id}",
                    "timestamp": self._parse_time(created_at),
                    "actor": sender or "user",
                    "action": "dm",
                    "details": {"conversation_id": conv_id, "text": text},
                }
                validate_story(event)
                events.append(event)
        return events
