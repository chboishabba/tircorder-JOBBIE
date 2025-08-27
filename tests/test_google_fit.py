from datetime import datetime, timedelta, timezone

import requests

from integrations.fitness.google_fit import GoogleFitConnector


class DummyResponse:
    def __init__(self, data):
        self._data = data

    def raise_for_status(self) -> None:  # pragma: no cover - no-op
        return None

    def json(self):
        return self._data


def test_metric_retrieval(monkeypatch):
    def fake_post(self, url, json, timeout):
        dtype = json["aggregateBy"][0]["dataTypeName"]
        if dtype == "com.google.step_count.delta":
            data = {
                "bucket": [
                    {
                        "startTimeMillis": "0",
                        "dataset": [{"point": [{"value": [{"intVal": 123}]}]}],
                    }
                ]
            }
        elif dtype == "com.google.heart_rate.bpm":
            data = {
                "bucket": [
                    {
                        "startTimeMillis": "0",
                        "dataset": [{"point": [{"value": [{"fpVal": 80.0}]}]}],
                    }
                ]
            }
        elif dtype == "com.google.sleep.segment":
            data = {
                "bucket": [
                    {
                        "startTimeMillis": "0",
                        "dataset": [{"point": [{"value": [{"intVal": 2}]}]}],
                    }
                ]
            }
        else:  # pragma: no cover - unexpected datatype
            raise AssertionError("unexpected data type")
        return DummyResponse(data)

    monkeypatch.setattr(requests.Session, "post", fake_post, raising=False)

    connector = GoogleFitConnector("token")
    start = datetime(2024, 1, 1, tzinfo=timezone.utc)
    end = start + timedelta(days=1)
    events = connector.get_metrics(start, end)
    assert len(events) == 3
    details = {e["details"]["metric"]: e["details"]["value"] for e in events}
    assert details["steps"] == 123
    assert details["heart_rate"] == 80.0
    assert details["sleep"] == 2
