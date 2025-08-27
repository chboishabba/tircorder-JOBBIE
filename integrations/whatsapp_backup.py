"""Parse WhatsApp chat exports into story events."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Set


TIMESTAMP_PATTERNS = [
    "%m/%d/%y, %I:%M %p",
    "%d/%m/%y, %I:%M %p",
    "%m/%d/%Y, %I:%M %p",
    "%d/%m/%Y, %I:%M %p",
    "%m/%d/%y, %H:%M",
    "%d/%m/%y, %H:%M",
    "%m/%d/%Y, %H:%M",
    "%d/%m/%Y, %H:%M",
    "%Y-%m-%dT%H:%M:%S",
    "%Y-%m-%dT%H:%M",
    "%Y-%m-%d %H:%M:%S",
    "%Y-%m-%d %H:%M",
]


@dataclass
class WhatsAppBackupConnector:
    """Convert WhatsApp chat export files into story events.

    The connector understands both the plain-text exports produced by the
    mobile app and simple JSON structures. Each parsed message becomes a
    dictionary with the keys required by the project-wide ``story`` schema.
    ``participants`` contains the set of distinct senders encountered during
    parsing which is useful for group chats.
    """

    chat_name: Optional[str] = None
    participants: Set[str] = field(default_factory=set)

    def parse(self, filepath: str | Path) -> List[Dict[str, Any]]:
        """Return story events from a WhatsApp export at *filepath*.

        Parameters
        ----------
        filepath:
            Path to the exported chat file which may be either plain-text
            or JSON. The format is detected automatically.
        """

        path = Path(filepath)
        content = path.read_text(encoding="utf-8")
        try:
            data = json.loads(content)
        except json.JSONDecodeError:
            return self._parse_text(content.splitlines())
        return self._parse_json(data)

    # ------------------------------------------------------------------
    def _parse_text(self, lines: Iterable[str]) -> List[Dict[str, Any]]:
        """Parse text export lines into story events."""

        events: List[Dict[str, Any]] = []
        pattern = re.compile(r"^(?P<ts>[^-]+) - (?P<rest>.+)$")
        for idx, line in enumerate(lines, 1):
            line = line.strip()
            if not line:
                continue
            match = pattern.match(line)
            if not match:
                continue
            ts_raw = match.group("ts").strip()
            rest = match.group("rest")
            if ": " in rest:
                sender, message = rest.split(": ", 1)
            else:
                sender, message = "system", rest
            timestamp = _parse_timestamp(ts_raw)
            event = _build_event(idx, timestamp, sender, message, self.chat_name)
            events.append(event)
            if sender != "system":
                self.participants.add(sender)
        return events

    # ------------------------------------------------------------------
    def _parse_json(self, data: Any) -> List[Dict[str, Any]]:
        """Parse JSON exports into story events."""

        messages = data.get("messages", data if isinstance(data, list) else [])
        events: List[Dict[str, Any]] = []
        for idx, msg in enumerate(messages, 1):
            sender = (
                msg.get("sender") or msg.get("from") or msg.get("author") or "system"
            )
            text = msg.get("text") or msg.get("message") or msg.get("body") or ""
            if isinstance(text, dict):
                text = text.get("body", "")
            ts_raw = msg.get("timestamp") or msg.get("time") or msg.get("created")
            if ts_raw is None:
                continue
            timestamp = _parse_timestamp(ts_raw)
            event = _build_event(idx, timestamp, sender, text, self.chat_name)
            events.append(event)
            if sender != "system":
                self.participants.add(sender)
        return events


# ----------------------------------------------------------------------
def _parse_timestamp(value: Any) -> datetime:
    """Return :class:`datetime` parsed from *value* using common formats."""

    if isinstance(value, (int, float)):
        return datetime.fromtimestamp(value)
    text = str(value).strip()
    for fmt in TIMESTAMP_PATTERNS:
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            continue
    try:
        return datetime.fromisoformat(text)
    except ValueError as exc:  # pragma: no cover - defensive programming
        raise ValueError(f"Unrecognised timestamp format: {value!r}") from exc


def _build_event(
    idx: int,
    timestamp: datetime,
    sender: str,
    message: str,
    chat_name: Optional[str],
) -> Dict[str, Any]:
    """Construct a story event dictionary."""

    details: Dict[str, Any] = {"message": message}
    if chat_name:
        details["chat"] = chat_name
    if "media omitted" in message.lower():
        details["media_omitted"] = True
    return {
        "event_id": f"wa-{idx}",
        "timestamp": timestamp.isoformat(),
        "actor": sender,
        "action": "message",
        "details": details,
    }
