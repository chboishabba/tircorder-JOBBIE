"""Google Fit activity connector.

This module provides :class:`GoogleFitConnector` for retrieving basic activity
metrics (steps, heart rate and sleep) from the Google Fit REST API.

Prerequisites
-------------
1. Create a project in `Google Cloud Console <https://console.cloud.google.com>`_.
2. Enable the **Fitness API** for the project.
3. Configure an OAuth consent screen and create OAuth client credentials.
4. Obtain an access token for the user with the following scopes:

   - ``https://www.googleapis.com/auth/fitness.activity.read``
   - ``https://www.googleapis.com/auth/fitness.heart_rate.read``
   - ``https://www.googleapis.com/auth/fitness.sleep.read``

The access token is supplied to :class:`GoogleFitConnector` which then performs
requests on behalf of the user.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

try:  # pragma: no cover - import exercised in tests
    import requests
except ImportError as exc:  # pragma: no cover - handled via tests
    raise ImportError(
        "The `requests` package is required to use the Google Fit integration. "
        "Install it with `pip install requests`."
    ) from exc

from tircorder.schemas import validate_story


class GoogleFitConnector:
    """Client for the Google Fit REST API."""

    BASE_URL = "https://www.googleapis.com/fitness/v1/users/me"

    def __init__(
        self, access_token: str, session: Optional[requests.Session] = None
    ) -> None:
        """Create a connector using *access_token* for authorization."""
        self.session = session or requests.Session()
        self.session.headers.update({"Authorization": f"Bearer {access_token}"})

    def _aggregate(
        self, data_type: str, start: datetime, end: datetime
    ) -> Dict[str, Any]:
        body = {
            "aggregateBy": [{"dataTypeName": data_type}],
            "startTimeMillis": int(start.timestamp() * 1000),
            "endTimeMillis": int(end.timestamp() * 1000),
        }
        response = self.session.post(
            f"{self.BASE_URL}/dataset:aggregate", json=body, timeout=10
        )
        response.raise_for_status()
        return response.json()

    def _metric(
        self, metric: str, data_type: str, start: datetime, end: datetime
    ) -> List[Dict[str, Any]]:
        data = self._aggregate(data_type, start, end)
        events: List[Dict[str, Any]] = []
        for bucket in data.get("bucket", []):
            start_ms = int(bucket.get("startTimeMillis", 0))
            ts = datetime.fromtimestamp(start_ms / 1000, tz=timezone.utc).isoformat()
            for dataset in bucket.get("dataset", []):
                for point in dataset.get("point", []):
                    value_field = point.get("value", [{}])[0]
                    val = value_field.get("intVal")
                    if val is None:
                        val = value_field.get("fpVal")
                    event = {
                        "event_id": f"google_fit_{metric}_{uuid4()}",
                        "timestamp": ts,
                        "actor": "user",
                        "action": "measure",
                        "details": {"metric": metric, "value": val},
                    }
                    validate_story(event)
                    events.append(event)
        return events

    def get_metrics(self, start: datetime, end: datetime) -> List[Dict[str, Any]]:
        """Return activity events for the given time range."""
        events: List[Dict[str, Any]] = []
        events.extend(self._metric("steps", "com.google.step_count.delta", start, end))
        events.extend(
            self._metric("heart_rate", "com.google.heart_rate.bpm", start, end)
        )
        events.extend(self._metric("sleep", "com.google.sleep.segment", start, end))
        return events
