"""Parse Slack workspace export archives."""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List
from uuid import uuid4

from tircorder.schemas import validate_story


class SlackBackupConnector:
    """Load messages from a Slack workspace export."""

    def __init__(self, export_path: str) -> None:
        self.export_path = Path(export_path)

    def load_messages(self) -> List[Dict]:
        """Return story events parsed from channel JSON files.

        The connector walks the export directory, reading each channel
        folder and its daily JSON message files. Messages are converted
        into story events compatible with ``story.schema.yaml``.
        """
        events: List[Dict] = []
        if not self.export_path.exists():
            return events
        for channel_dir in sorted(self.export_path.iterdir()):
            if not channel_dir.is_dir() or channel_dir.name == "files":
                continue
            channel = channel_dir.name
            for page in sorted(channel_dir.glob("*.json")):
                with page.open("r", encoding="utf-8") as fh:
                    messages = json.load(fh)
                for msg in messages:
                    ts = msg.get("ts")
                    if not ts:
                        continue
                    try:
                        timestamp = datetime.fromtimestamp(float(ts)).isoformat()
                    except (TypeError, ValueError):
                        continue
                    subtype = msg.get("subtype")
                    if subtype == "bot_message":
                        actor = f"bot:{msg.get('bot_id', 'unknown')}"
                    elif subtype:
                        actor = "system"
                    else:
                        actor = msg.get("user", "system")
                    details = {"channel": channel, "text": msg.get("text", "")}
                    files = []
                    for file in msg.get("files", []):
                        name = file.get("name") or file.get("title")
                        file_id = file.get("id")
                        candidate = (
                            self.export_path / "files" / (file_id or "") / (name or "")
                        )
                        files.append(str(candidate) if candidate.exists() else name)
                    if files:
                        details["files"] = files
                    event = {
                        "event_id": f"slack_{uuid4()}",
                        "timestamp": timestamp,
                        "actor": actor,
                        "action": "message",
                        "details": details,
                    }
                    validate_story(event)
                    events.append(event)
        return events
