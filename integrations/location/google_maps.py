"""Parse Google Maps location history exports."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from uuid import uuid4

from tircorder.schemas import validate_story


class GoogleMapsConnector:
    """Normalize Google Maps Takeout location history."""

    def load(self, path: str | Path) -> List[Dict]:
        """Load events from a Takeout export.

        Parameters
        ----------
        path:
            Path to ``Location History.json`` or ``Semantic Location History`` directory.

        Returns
        -------
        list of dict
            Story events with ``timestamp``, ``lat``, ``lon`` and ``place`` details.
        """

        p = Path(path)
        if p.is_dir():
            return self._load_semantic(p)
        return self._load_location_history(p)

    # ------------------------------------------------------------------
    def _load_location_history(self, file_path: Path) -> List[Dict]:
        """Parse ``Location History.json`` exports."""

        with open(file_path, "r", encoding="utf-8") as fh:
            data = json.load(fh)

        events: List[Dict] = []
        for item in data.get("locations", []):
            event = self._build_event(
                item.get("timestampMs"),
                item.get("latitudeE7"),
                item.get("longitudeE7"),
                item.get("source", ""),
            )
            if event:
                events.append(event)
        return events

    # ------------------------------------------------------------------
    def _load_semantic(self, folder: Path) -> List[Dict]:
        """Parse ``Semantic Location History`` directories."""

        events: List[Dict] = []
        for json_file in sorted(folder.glob("**/*.json")):
            try:
                with open(json_file, "r", encoding="utf-8") as fh:
                    data = json.load(fh)
            except json.JSONDecodeError:
                continue
            for obj in data.get("timelineObjects", []):
                if "placeVisit" in obj:
                    pv = obj["placeVisit"]
                    loc = pv.get("location", {})
                    dur = pv.get("duration", {})
                    event = self._build_event(
                        dur.get("startTimestampMs"),
                        loc.get("latitudeE7"),
                        loc.get("longitudeE7"),
                        loc.get("name", ""),
                    )
                    if event:
                        events.append(event)
                elif "activitySegment" in obj:
                    seg = obj["activitySegment"]
                    dur = seg.get("duration", {})
                    start = seg.get("startLocation", {})
                    end = seg.get("endLocation", {})
                    event = self._build_event(
                        dur.get("startTimestampMs"),
                        start.get("latitudeE7"),
                        start.get("longitudeE7"),
                        start.get("name", ""),
                    )
                    if event:
                        events.append(event)
                    event_end = self._build_event(
                        dur.get("endTimestampMs"),
                        end.get("latitudeE7"),
                        end.get("longitudeE7"),
                        end.get("name", ""),
                    )
                    if event_end:
                        events.append(event_end)
                    for point in seg.get("waypointPath", {}).get("points", []):
                        wp_event = self._build_event(
                            dur.get("startTimestampMs"),
                            point.get("latE7"),
                            point.get("lngE7"),
                            "",
                        )
                        if wp_event:
                            events.append(wp_event)
        return events

    # ------------------------------------------------------------------
    def _build_event(
        self,
        timestamp_ms: Optional[str],
        lat_e7: Optional[int],
        lon_e7: Optional[int],
        place: str,
    ) -> Optional[Dict]:
        """Construct a story event or return ``None`` if data is invalid."""

        try:
            if timestamp_ms is None or lat_e7 is None or lon_e7 is None:
                return None
            dt = datetime.utcfromtimestamp(int(timestamp_ms) / 1000)
            lat = int(lat_e7) / 1e7
            lon = int(lon_e7) / 1e7
        except (ValueError, TypeError):
            return None
        event = {
            "event_id": f"google_maps_{uuid4()}",
            "timestamp": dt.isoformat() + "+00:00",
            "actor": "user",
            "action": "location",
            "details": {"lat": lat, "lon": lon, "place": place},
        }
        try:
            validate_story(event)
        except Exception:
            return None
        return event
