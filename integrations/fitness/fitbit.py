"""Fitbit activity connector."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Dict, List, Optional
from uuid import uuid4

import requests

from tircorder.schemas import validate_story


class FitbitConnector:
    """Interact with the Fitbit Web API."""

    token_url = "https://api.fitbit.com/oauth2/token"
    api_base = "https://api.fitbit.com/1"

    def __init__(self, client_id: str, client_secret: str, redirect_uri: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.access_token: Optional[str] = None
        self.refresh_token: Optional[str] = None
        self.expires_at: Optional[datetime] = None

    def authenticate(self, code: Optional[str] = None) -> None:
        """Authenticate or refresh the Fitbit access token.

        Parameters
        ----------
        code:
            Authorization code obtained from the OAuth2 redirect. If omitted the
            existing refresh token will be used to obtain a new access token.
        """

        data = {"client_id": self.client_id}
        if self.refresh_token and not code:
            data.update(
                {"grant_type": "refresh_token", "refresh_token": self.refresh_token}
            )
        elif code:
            data.update(
                {
                    "grant_type": "authorization_code",
                    "redirect_uri": self.redirect_uri,
                    "code": code,
                }
            )
        else:
            raise ValueError("No authorization code or refresh token available")

        try:
            response = requests.post(
                self.token_url,
                data=data,
                auth=(self.client_id, self.client_secret),
                timeout=10,
            )
            response.raise_for_status()
        except requests.RequestException as exc:
            raise RuntimeError("Fitbit authentication failed") from exc

        token_data = response.json()
        self.access_token = token_data.get("access_token")
        self.refresh_token = token_data.get("refresh_token", self.refresh_token)
        expires_in = token_data.get("expires_in", 0)
        self.expires_at = datetime.utcnow() + timedelta(seconds=int(expires_in))

    def _get(self, endpoint: str) -> Optional[Dict]:
        if not self.access_token:
            raise RuntimeError("Not authenticated")
        headers = {"Authorization": f"Bearer {self.access_token}"}
        url = f"{self.api_base}{endpoint}"
        try:
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 401 and self.refresh_token:
                self.authenticate()
                headers["Authorization"] = f"Bearer {self.access_token}"
                response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 429:
                return None
            response.raise_for_status()
            return response.json()
        except requests.RequestException:
            return None

    def fetch_steps(self, date: str) -> List[Dict]:
        """Fetch daily step counts for ``date`` (YYYY-MM-DD)."""

        data = self._get(f"/activities/steps/date/{date}/1d.json") or {}
        events: List[Dict] = []
        for item in data.get("activities-steps", []):
            dt = datetime.fromisoformat(item["dateTime"])
            event = {
                "event_id": f"fitbit_steps_{uuid4()}",
                "timestamp": dt.isoformat(),
                "actor": "fitbit",
                "action": "steps",
                "details": {"count": int(item.get("value", 0))},
            }
            validate_story(event)
            events.append(event)
        return events

    def fetch_heart_rate(self, date: str) -> List[Dict]:
        """Fetch resting heart rate for ``date`` (YYYY-MM-DD)."""

        data = self._get(f"/activities/heart/date/{date}/1d.json") or {}
        events: List[Dict] = []
        for item in data.get("activities-heart", []):
            dt = datetime.fromisoformat(item["dateTime"])
            resting = item.get("value", {}).get("restingHeartRate")
            event = {
                "event_id": f"fitbit_hr_{uuid4()}",
                "timestamp": dt.isoformat(),
                "actor": "fitbit",
                "action": "heart_rate",
                "details": {"resting_heart_rate": resting},
            }
            validate_story(event)
            events.append(event)
        return events

    def fetch_sleep(self, date: str) -> List[Dict]:
        """Fetch sleep summary for ``date`` (YYYY-MM-DD)."""

        data = self._get(f"/sleep/date/{date}.json") or {}
        events: List[Dict] = []
        for item in data.get("sleep", []):
            dt = datetime.fromisoformat(item.get("dateOfSleep"))
            event = {
                "event_id": f"fitbit_sleep_{uuid4()}",
                "timestamp": dt.isoformat(),
                "actor": "fitbit",
                "action": "sleep",
                "details": {"minutes_asleep": item.get("minutesAsleep")},
            }
            validate_story(event)
            events.append(event)
        return events
