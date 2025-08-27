from pathlib import Path

import pytest

from integrations.location.google_maps import GoogleMapsConnector


def test_load_location_history():
    connector = GoogleMapsConnector()
    path = Path(__file__).parent / "data" / "google_maps" / "Location History.json"
    events = connector.load(path)
    assert len(events) == 2
    first = events[0]
    assert first["actor"] == "user"
    assert first["action"] == "location"
    assert first["details"]["place"] == "GPS"
    assert first["details"]["lat"] == pytest.approx(37.77, rel=1e-3)
    assert first["details"]["lon"] == pytest.approx(-122.4194, rel=1e-3)


def test_load_semantic_location_history():
    connector = GoogleMapsConnector()
    folder = (
        Path(__file__).parent / "data" / "google_maps" / "Semantic Location History"
    )
    events = connector.load(folder)
    assert len(events) == 4
    places = {e["details"]["place"] for e in events}
    assert "Home" in places
    # Waypoint path should produce an event without place name
    assert "" in places
