"""Parse Instagram data download JSON exports into story events."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

from tircorder.schemas import validate_story


class InstagramBackupConnector:
    """Load posts, stories and messages from an Instagram data download."""

    def __init__(self, base_path: str | Path) -> None:
        """Initialise connector with the path to an export directory."""
        self.base_path = Path(base_path)

    def load(self) -> List[Dict[str, Any]]:
        """Return validated story events from the export directory."""
        events: List[Dict[str, Any]] = []
        events.extend(self._load_items(self.base_path / "posts.json", "post"))
        events.extend(self._load_items(self.base_path / "stories.json", "story"))
        events.extend(self._load_items(self.base_path / "messages.json", "message"))
        return events

    def _load_items(self, filepath: Path, action: str) -> List[Dict[str, Any]]:
        """Parse *filepath* for events with the given *action*."""
        if not filepath.exists():
            return []
        with open(filepath, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        events: List[Dict[str, Any]] = []
        for item in data:
            timestamp = item.get("timestamp")
            if not timestamp:
                raise ValueError(f"Missing timestamp in {action} item: {item}")
            if action in {"post", "story"} and not item.get("media"):
                raise ValueError(f"Missing media in {action} item at {timestamp}")
            event: Dict[str, Any] = {
                "event_id": str(item.get("id", "")),
                "timestamp": timestamp,
                "actor": "instagram",
                "action": action,
                "details": {
                    k: v for k, v in item.items() if k not in {"id", "timestamp"}
                },
            }
            validate_story(event)
            events.append(event)
        return events
