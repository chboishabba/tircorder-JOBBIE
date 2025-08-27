"""Apple Health integration utilities."""

from __future__ import annotations

from datetime import datetime
from typing import Dict, List
from uuid import uuid4
from xml.etree import ElementTree as ET

from tircorder.schemas import validate_story


class AppleHealthConnector:
    """Parse data from Apple Health exports or a native bridge."""

    def fetch_bridge(self) -> List[Dict]:
        """Placeholder for a native bridge integration."""
        raise NotImplementedError("Native bridge integration not yet implemented")

    def load_export(self, path: str) -> List[Dict]:
        """Load events from a HealthKit ``export.xml`` file.

        Parameters
        ----------
        path:
            Location of the ``export.xml`` file.

        Returns
        -------
        list of dict
            Story events parsed from the file.

        Raises
        ------
        ValueError
            If the XML is malformed or cannot be read.
        """

        try:
            root = ET.parse(path).getroot()
        except (
            ET.ParseError,
            FileNotFoundError,
        ) as exc:  # pragma: no cover - file missing
            raise ValueError("Invalid HealthKit export") from exc

        events: List[Dict] = []

        for record in root.findall("Record"):
            rtype = record.get("type")
            start = record.get("startDate")
            end = record.get("endDate")
            if not rtype or not start:
                continue
            try:
                ts = datetime.fromisoformat(start.replace("Z", "+00:00"))
            except ValueError:
                continue

            if rtype == "HKQuantityTypeIdentifierStepCount":
                value = record.get("value")
                if value is None:
                    continue
                event = {
                    "event_id": f"apple_health_steps_{uuid4()}",
                    "timestamp": ts.isoformat(),
                    "actor": "user",
                    "action": "steps",
                    "details": {"count": int(value), "start": start, "end": end},
                }
                validate_story(event)
                events.append(event)

            elif rtype == "HKQuantityTypeIdentifierHeartRate":
                value = record.get("value")
                unit = record.get("unit")
                if value is None:
                    continue
                event = {
                    "event_id": f"apple_health_hr_{uuid4()}",
                    "timestamp": ts.isoformat(),
                    "actor": "user",
                    "action": "heart_rate",
                    "details": {"bpm": float(value), "unit": unit},
                }
                validate_story(event)
                events.append(event)

            elif rtype == "HKCategoryTypeIdentifierSleepAnalysis":
                state = record.get("value")
                if state is None:
                    continue
                event = {
                    "event_id": f"apple_health_sleep_{uuid4()}",
                    "timestamp": ts.isoformat(),
                    "actor": "user",
                    "action": "sleep",
                    "details": {"state": state, "start": start, "end": end},
                }
                validate_story(event)
                events.append(event)

        for workout in root.findall("Workout"):
            start = workout.get("startDate")
            if not start:
                continue
            try:
                ts = datetime.fromisoformat(start.replace("Z", "+00:00"))
            except ValueError:
                continue
            activity = workout.get("workoutActivityType", "")
            details = {
                "activity": activity.replace("HKWorkoutActivityType", "").lower(),
                "duration": _to_float(workout.get("duration")),
                "energy_burned": _to_float(workout.get("totalEnergyBurned")),
                "distance": _to_float(workout.get("totalDistance")),
            }
            event = {
                "event_id": f"apple_health_workout_{uuid4()}",
                "timestamp": ts.isoformat(),
                "actor": "user",
                "action": "workout",
                "details": details,
            }
            validate_story(event)
            events.append(event)

        return events


def _to_float(value: str | None) -> float | None:
    """Convert *value* to ``float`` if possible."""

    if value is None:
        return None
    try:
        return float(value)
    except ValueError:
        return None
