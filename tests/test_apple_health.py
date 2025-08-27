from pathlib import Path

import pytest

from integrations.fitness.apple_health import AppleHealthConnector


def test_load_export():
    connector = AppleHealthConnector()
    path = Path("tests/data/apple_health_export.xml")
    events = connector.load_export(str(path))
    assert len(events) == 4
    actions = {e["action"] for e in events}
    assert actions == {"steps", "heart_rate", "sleep", "workout"}
    step_event = next(e for e in events if e["action"] == "steps")
    assert step_event["details"]["count"] == 100
    workout_event = next(e for e in events if e["action"] == "workout")
    assert workout_event["details"]["activity"] == "running"


def test_load_export_bad_xml(tmp_path):
    bad = tmp_path / "bad.xml"
    bad.write_text("<HealthData><Record></HealthData>", encoding="utf-8")
    connector = AppleHealthConnector()
    with pytest.raises(ValueError):
        connector.load_export(str(bad))
