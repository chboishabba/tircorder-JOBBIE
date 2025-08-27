"""Foursquare check-in integration.

This connector uses OAuth to obtain an access token and retrieve a user's
check-ins. Foursquare requires a version string (``v``) in YYYYMMDD format for
all API calls. The free tier allows roughly 95 requests per minute and about
5,000 requests per day before returning HTTP 429 responses.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict, List, Optional
from urllib.parse import urlencode

try:  # pragma: no cover - exercised in import tests
    import requests
except ImportError as exc:  # pragma: no cover - handled via tests
    raise ImportError(
        "The `requests` package is required to use the Foursquare integration. "
        "Install it with `pip install requests`."
    ) from exc

from tircorder.schemas import validate_story


class FoursquareConnector:
    """Client for Foursquare check-ins.

    Parameters
    ----------
    client_id:
        OAuth client identifier.
    client_secret:
        OAuth client secret.
    redirect_uri:
        URI registered with the Foursquare application.
    api_version:
        API version string in ``YYYYMMDD`` format. Defaults to ``20240601``.

    Notes
    -----
    The Foursquare API enforces rate limits. Applications on the free tier are
    limited to approximately 95 requests per minute and 5,000 requests per day.
    """

    API_BASE = "https://api.foursquare.com/v2"
    AUTH_URL = "https://foursquare.com/oauth2/authorize"
    TOKEN_URL = "https://foursquare.com/oauth2/access_token"

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        redirect_uri: str,
        *,
        api_version: str = "20240601",
    ) -> None:
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.api_version = api_version
        self.access_token: Optional[str] = None

    def get_auth_url(self) -> str:
        """Return the OAuth authorization URL for user login."""
        params = {
            "client_id": self.client_id,
            "response_type": "code",
            "redirect_uri": self.redirect_uri,
        }
        return f"{self.AUTH_URL}?{urlencode(params)}"

    def exchange_code(self, code: str) -> str:
        """Exchange an OAuth *code* for an access token."""
        data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "grant_type": "authorization_code",
            "redirect_uri": self.redirect_uri,
            "code": code,
        }
        response = requests.post(self.TOKEN_URL, data=data, timeout=10)
        response.raise_for_status()
        token = response.json()["access_token"]
        self.access_token = token
        return token

    def fetch_checkins(self, limit: int = 250) -> List[Dict]:
        """Return recent check-ins for the authenticated user."""
        if not self.access_token:
            raise RuntimeError("Access token missing. Call `exchange_code` first.")
        params = {
            "oauth_token": self.access_token,
            "v": self.api_version,
            "limit": limit,
        }
        response = requests.get(
            f"{self.API_BASE}/users/self/checkins", params=params, timeout=10
        )
        response.raise_for_status()
        data = response.json()
        return data.get("response", {}).get("checkins", {}).get("items", [])

    @staticmethod
    def checkin_to_event(checkin: Dict) -> Dict:
        """Convert a check-in record into a validated story event."""
        venue = checkin.get("venue", {})
        location = venue.get("location", {})
        event = {
            "event_id": f"foursquare_{checkin['id']}",
            "timestamp": datetime.fromtimestamp(
                checkin["createdAt"], tz=timezone.utc
            ).isoformat(),
            "actor": "user",
            "action": "check-in",
            "details": {
                "venue": venue.get("name"),
                "lat": location.get("lat"),
                "lon": location.get("lng"),
            },
        }
        validate_story(event)
        return event

    def fetch_events(self, limit: int = 250) -> List[Dict]:
        """Retrieve check-ins and return them as validated story events."""
        checkins = self.fetch_checkins(limit=limit)
        return [self.checkin_to_event(item) for item in checkins]
