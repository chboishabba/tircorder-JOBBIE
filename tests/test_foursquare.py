from __future__ import annotations

from unittest.mock import Mock, patch

from integrations.location.foursquare import FoursquareConnector

FAKE_CHECKIN = {
    "id": "1",
    "createdAt": 1_714_721_600,
    "venue": {
        "name": "Central Perk",
        "location": {"lat": 40.0, "lng": -73.0},
    },
}


@patch("integrations.location.foursquare.requests.post")
def test_exchange_code_sets_token(mock_post: Mock) -> None:
    connector = FoursquareConnector("id", "secret", "http://localhost")
    mock_resp = Mock()
    mock_resp.json.return_value = {"access_token": "abc"}
    mock_resp.raise_for_status.return_value = None
    mock_post.return_value = mock_resp

    token = connector.exchange_code("CODE")
    assert token == "abc"
    assert connector.access_token == "abc"


@patch("integrations.location.foursquare.requests.get")
def test_fetch_events(mock_get: Mock) -> None:
    connector = FoursquareConnector("id", "secret", "http://localhost")
    connector.access_token = "TOKEN"

    mock_resp = Mock()
    mock_resp.json.return_value = {"response": {"checkins": {"items": [FAKE_CHECKIN]}}}
    mock_resp.raise_for_status.return_value = None
    mock_get.return_value = mock_resp

    events = connector.fetch_events()
    assert len(events) == 1
    event = events[0]
    assert event["details"]["venue"] == "Central Perk"
    assert event["details"]["lat"] == 40.0
    assert event["details"]["lon"] == -73.0
