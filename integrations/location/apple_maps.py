"""Connector for parsing Apple Maps history from device backups."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional
from uuid import uuid4
import plistlib

from tircorder.schemas import validate_story


class AppleMapsConnector:
    """Load route and search history from Apple Maps backups."""

    def load_history(self, backup_dir: str | Path) -> List[Dict]:
        """Parse maps history from ``backup_dir``.

        Parameters
        ----------
        backup_dir:
            Directory containing ``MapsHistory.plist`` or ``Maps/History``.

        Returns
        -------
        list of dict
            Story events extracted from the history file.
        """

        history_file = self._find_history_file(Path(backup_dir))
        if history_file is None:
            return []

        with open(history_file, "rb") as fh:
            raw = plistlib.load(fh)

        items = raw.get("historyItems") or raw.get("MSPHistoryItems") or []
        events: List[Dict] = []
        for item in items:
            if item.get("isPrivate"):
                continue

            dt = self._normalize_time(item)
            if dt is None:
                continue

            action = "navigate" if item.get("type") == "route" else "search"
            details: Dict[str, str] = {}
            if action == "navigate":
                start = item.get("start") or item.get("origin")
                end = item.get("end") or item.get("destination")
                if start:
                    details["start"] = start
                if end:
                    details["end"] = end
            else:
                query = item.get("query") or item.get("displayTitle")
                if query:
                    details["query"] = query

            event = {
                "event_id": f"apple_maps_{uuid4()}",
                "timestamp": dt.isoformat(),
                "actor": "user",
                "action": action,
                "details": details,
            }
            validate_story(event)
            events.append(event)

        return events

    def _find_history_file(self, root: Path) -> Optional[Path]:
        """Locate the maps history file within ``root``."""
        candidates = [root / "MapsHistory.plist", root / "Maps" / "History"]
        for path in candidates:
            if path.exists():
                return path
        return None

    def _normalize_time(self, item: Dict) -> Optional[datetime]:
        """Return event time in UTC for ``item``."""
        dt = item.get("timestamp") or item.get("date")
        if isinstance(dt, datetime):
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            else:
                dt = dt.astimezone(timezone.utc)
            return dt
        if isinstance(dt, str):
            try:
                parsed = datetime.fromisoformat(dt)
            except ValueError:
                return None
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=timezone.utc)
            else:
                parsed = parsed.astimezone(timezone.utc)
            return parsed
        return None
