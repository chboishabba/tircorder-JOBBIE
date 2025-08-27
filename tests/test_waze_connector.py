from pathlib import Path

from integrations.location.waze import WazeConnector


def test_parse_drive_history(tmp_path):
    sample = Path(__file__).parent / "data" / "waze_sample.json"
    connector = WazeConnector()
    events = connector.parse_drive_history(str(sample))
    assert len(events) == 2

    first = events[0]["details"]
    assert first["distance_m"] == 15000.0
    assert first["duration_s"] == 1800
    assert first["start_point"] == {"lat": 34.0, "lon": -118.0}
    assert first["end_point"] == {"lat": 34.1, "lon": -118.1}

    second = events[1]["details"]
    assert second["start_point"] is None
    assert second["end_point"] is None
