from pathlib import Path

from integrations.location.apple_maps import AppleMapsConnector


def test_load_history_plist():
    connector = AppleMapsConnector()
    backup_dir = Path(__file__).parent / "data" / "backup_plist"
    events = connector.load_history(backup_dir)
    assert len(events) == 2
    search_event = next(e for e in events if e["action"] == "search")
    assert search_event["details"]["query"] == "Coffee Shop"
    assert search_event["timestamp"].endswith("+00:00")
    route_event = next(e for e in events if e["action"] == "navigate")
    assert route_event["details"]["start"] == "Home"
    assert route_event["details"]["end"] == "Office"


def test_load_history_folder():
    connector = AppleMapsConnector()
    backup_dir = Path(__file__).parent / "data" / "backup_folder"
    events = connector.load_history(backup_dir)
    assert len(events) == 2
