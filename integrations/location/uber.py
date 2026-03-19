"""Uber trip history connector."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import requests

TOKEN_URL = "https://login.uber.com/oauth/v2/token"
TRIPS_URL = "https://api.uber.com/v1.2/history"
RECEIPT_URL = "https://api.uber.com/v1.2/requests/{request_id}/receipt"


class UberConnector:
    """Connector for fetching a user's Uber trip history."""

    access_token: Optional[str]

    def __init__(self) -> None:
        self.access_token = None

    # ------------------------------------------------------------------
    def authenticate(
        self, client_id: str, client_secret: str, refresh_token: str
    ) -> None:
        """Authenticate with Uber using OAuth refresh token.

        Parameters
        ----------
        client_id:
            OAuth client ID.
        client_secret:
            OAuth client secret.
        refresh_token:
            Refresh token obtained from the OAuth dance.
        """

        data = {
            "client_id": client_id,
            "client_secret": client_secret,
            "refresh_token": refresh_token,
            "grant_type": "refresh_token",
        }
        response = requests.post(TOKEN_URL, data=data, timeout=10)
        response.raise_for_status()
        token = response.json().get("access_token")
        if not token:
            raise ValueError("access_token missing from response")
        self.access_token = token

    # ------------------------------------------------------------------
    def fetch_trips(
        self, start_time: datetime, end_time: datetime
    ) -> List[Dict[str, Any]]:
        """Return trip history between ``start_time`` and ``end_time``.

        Each trip is converted into a timeline event dictionary containing
        pickup/dropoff times and locations.  If receipt information is
        available, price and currency will also be included.
        """

        if not self.access_token:
            raise RuntimeError("authenticate() must be called first")

        start_ts = self._to_unix_seconds(start_time)
        end_ts = self._to_unix_seconds(end_time)

        headers = {"Authorization": f"Bearer {self.access_token}"}
        params = {
            "start_time": start_ts,
            "end_time": end_ts,
        }
        response = requests.get(TRIPS_URL, headers=headers, params=params, timeout=10)
        response.raise_for_status()
        trips = response.json().get("trips", [])

        events: List[Dict[str, Any]] = []
        for trip in trips:
            try:
                event = self._trip_to_event(trip, headers)
            except KeyError:
                continue
            events.append(event)
        return events

    # ------------------------------------------------------------------
    @staticmethod
    def _to_unix_seconds(value: datetime) -> int:
        """Convert a datetime to Unix seconds, treating naive values as UTC."""

        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        else:
            value = value.astimezone(timezone.utc)
        return int(value.timestamp())

    # ------------------------------------------------------------------
    def _trip_to_event(
        self, trip: Dict[str, Any], headers: Dict[str, str]
    ) -> Dict[str, Any]:
        """Convert a single trip record to a timeline event."""

        pickup = trip["pickup"]
        dropoff = trip["dropoff"]
        event: Dict[str, Any] = {
            "pickup_time": datetime.fromtimestamp(trip["start_time"], tz=timezone.utc),
            "dropoff_time": datetime.fromtimestamp(trip["end_time"], tz=timezone.utc),
            "pickup_location": {
                "lat": pickup["latitude"],
                "lng": pickup["longitude"],
            },
            "dropoff_location": {
                "lat": dropoff["latitude"],
                "lng": dropoff["longitude"],
            },
        }

        request_id = trip.get("request_id")
        if request_id:
            receipt = self._fetch_receipt(request_id, headers)
            if receipt:
                price = receipt.get("total_charged")
                try:
                    event["price"] = float(price)
                except (TypeError, ValueError):
                    pass
                event["currency"] = receipt.get("currency_code")
                event["receipt_id"] = receipt.get("receipt_id")
        return event

    # ------------------------------------------------------------------
    def _fetch_receipt(
        self, request_id: str, headers: Dict[str, str]
    ) -> Optional[Dict[str, Any]]:
        """Fetch receipt details for *request_id*.

        Returns ``None`` if the request fails.
        """

        url = RECEIPT_URL.format(request_id=request_id)
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code != 200:  # pragma: no cover - network failure
            return None
        return response.json()
