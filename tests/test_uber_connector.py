from datetime import datetime
import requests
import pytest

from integrations.location.uber import (
    RECEIPT_URL,
    TOKEN_URL,
    TRIPS_URL,
    UberConnector,
)


class DummyResponse:
    def __init__(self, data, status_code=200):
        self._data = data
        self.status_code = status_code

    def raise_for_status(self):  # pragma: no cover - no error in tests
        if self.status_code >= 400:
            raise requests.HTTPError(self.status_code)

    def json(self):
        return self._data


def test_fetch_trips_success(monkeypatch):
    connector = UberConnector()

    def fake_post(url, data=None, timeout=0):
        assert url == TOKEN_URL
        return DummyResponse({"access_token": "TOKEN"})

    monkeypatch.setattr(requests, "post", fake_post)
    connector.authenticate("id", "secret", "refresh")

    trips_payload = {
        "trips": [
            {
                "start_time": 1609459200,
                "end_time": 1609462800,
                "pickup": {"latitude": 37.0, "longitude": -122.0},
                "dropoff": {"latitude": 38.0, "longitude": -123.0},
                "request_id": "REQ1",
            }
        ]
    }

    receipt_payload = {
        "total_charged": "15.50",
        "currency_code": "USD",
        "receipt_id": "REC1",
    }

    def fake_get(url, headers=None, params=None, timeout=0):
        if url == TRIPS_URL:
            assert headers["Authorization"] == "Bearer TOKEN"
            assert params["start_time"] == 1609459200
            assert params["end_time"] == 1609545600
            return DummyResponse(trips_payload)
        if url == RECEIPT_URL.format(request_id="REQ1"):
            return DummyResponse(receipt_payload)
        raise AssertionError(f"unexpected url {url}")

    monkeypatch.setattr(requests, "get", fake_get)

    events = connector.fetch_trips(datetime(2021, 1, 1), datetime(2021, 1, 2))

    assert len(events) == 1
    ev = events[0]
    assert ev["pickup_location"]["lat"] == 37.0
    assert ev["dropoff_location"]["lng"] == -123.0
    assert ev["price"] == 15.5
    assert ev["currency"] == "USD"
    assert ev["receipt_id"] == "REC1"


def test_requires_authentication():
    connector = UberConnector()
    with pytest.raises(RuntimeError):
        connector.fetch_trips(datetime(2021, 1, 1), datetime(2021, 1, 2))
