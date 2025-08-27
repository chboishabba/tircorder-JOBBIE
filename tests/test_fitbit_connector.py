import requests
from integrations.fitness import fitbit as fitbit_module
from integrations.fitness import FitbitConnector
from unittest.mock import Mock


class DummyResponse:
    def __init__(self, payload, status_code=200):
        self._payload = payload
        self.status_code = status_code

    def json(self):
        return self._payload

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(self.status_code)


def test_fetch_steps_event_structure(monkeypatch):
    connector = FitbitConnector("id", "secret", "https://example.com")
    connector.access_token = "token"
    sample = {"activities-steps": [{"dateTime": "2024-05-01", "value": "123"}]}

    monkeypatch.setattr(requests, "get", lambda *a, **k: DummyResponse(sample))
    mocked = Mock()
    monkeypatch.setattr(fitbit_module, "validate_story", mocked)

    events = connector.fetch_steps("2024-05-01")
    assert events[0]["action"] == "steps"
    mocked.assert_called_once_with(events[0])


def test_fetch_heart_rate_event_structure(monkeypatch):
    connector = FitbitConnector("id", "secret", "https://example.com")
    connector.access_token = "token"
    sample = {
        "activities-heart": [
            {"dateTime": "2024-05-01", "value": {"restingHeartRate": 60}}
        ]
    }

    monkeypatch.setattr(requests, "get", lambda *a, **k: DummyResponse(sample))
    mocked = Mock()
    monkeypatch.setattr(fitbit_module, "validate_story", mocked)

    events = connector.fetch_heart_rate("2024-05-01")
    assert events[0]["action"] == "heart_rate"
    mocked.assert_called_once_with(events[0])


def test_fetch_sleep_event_structure(monkeypatch):
    connector = FitbitConnector("id", "secret", "https://example.com")
    connector.access_token = "token"
    sample = {"sleep": [{"dateOfSleep": "2024-05-01", "minutesAsleep": 400}]}

    monkeypatch.setattr(requests, "get", lambda *a, **k: DummyResponse(sample))
    mocked = Mock()
    monkeypatch.setattr(fitbit_module, "validate_story", mocked)

    events = connector.fetch_sleep("2024-05-01")
    assert events[0]["action"] == "sleep"
    mocked.assert_called_once_with(events[0])
