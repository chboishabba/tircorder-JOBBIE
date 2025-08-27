"""Parse Waze drive history exports into story events."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4

from tircorder.schemas import validate_story


class WazeConnector:
    """Parse Waze drive history exports."""

    def parse_drive_history(self, path: str) -> List[Dict[str, Any]]:
        """Return story events for each drive in the Waze export at ``path``.

        Parameters
        ----------
        path:
            Location of the JSON file exported from Waze.

        Returns
        -------
        list of dict
            Story events with distance and duration details.

        Notes
        -----
        Drives missing timestamps or distance are skipped. Segments with
        missing coordinates are ignored when determining start and end points.
        """

        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)

        drives = data.get("drives") or data.get("userTrips") or []
        events: List[Dict[str, Any]] = []
        for drive in drives:
            start = self._parse_time(
                drive.get("startTime") or drive.get("startTimeMillis")
            )
            end = self._parse_time(drive.get("endTime") or drive.get("endTimeMillis"))
            length = drive.get("lengthMeters") or drive.get("length")
            if not (start and end and length):
                continue

            duration_s = int((end - start).total_seconds())
            distance_m = float(length)
            start_point, end_point = self._extract_points(
                drive.get("segments") or drive.get("path") or []
            )
            event: Dict[str, Any] = {
                "event_id": f"waze_drive_{uuid4()}",
                "timestamp": start.isoformat(),
                "actor": "user",
                "action": "drive",
                "details": {
                    "distance_m": distance_m,
                    "duration_s": duration_s,
                    "start_point": start_point,
                    "end_point": end_point,
                },
            }
            validate_story(event)
            events.append(event)
        return events

    @staticmethod
    def _parse_time(value: Any) -> Optional[datetime]:
        """Parse timestamp from ISO string or milliseconds."""
        if value is None:
            return None
        if isinstance(value, (int, float)):
            try:
                return datetime.fromtimestamp(value / 1000, tz=timezone.utc)
            except OSError:
                return None
        if isinstance(value, str):
            try:
                return datetime.fromisoformat(value.replace("Z", "+00:00"))
            except ValueError:
                return None
        return None

    @staticmethod
    def _extract_points(
        segments: List[Any],
    ) -> Tuple[Optional[Dict[str, float]], Optional[Dict[str, float]]]:
        """Return the first and last valid coordinates from ``segments``."""
        points = [
            {
                "lat": seg.get("lat") or seg.get("latitude"),
                "lon": seg.get("lon") or seg.get("longitude"),
            }
            for seg in segments
            if isinstance(seg, dict)
            and isinstance(seg.get("lat") or seg.get("latitude"), (int, float))
            and isinstance(seg.get("lon") or seg.get("longitude"), (int, float))
        ]
        if not points:
            return None, None
        return points[0], points[-1]
