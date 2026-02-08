from datetime import datetime, timezone

from integrations.medical import ScanFolderConnector


def test_scan_folder_emits_hashed_events_with_filename_timestamp(tmp_path):
    scan_dir = tmp_path / "scans"
    scan_dir.mkdir()
    path = scan_dir / "2026-02-01_knee_scan.dcm"
    path.write_bytes(b"not real dicom")

    collected_at = datetime(2026, 2, 8, 12, 0, 0, tzinfo=timezone.utc)
    connector = ScanFolderConnector(scan_dir)
    events = connector.load(collected_at=collected_at)

    assert len(events) == 1
    event = events[0]
    assert event["action"] == "medical_scan"
    assert event["timestamp"] == "2026-02-01T00:00:00+00:00"
    assert event["details"]["sha256"]
    assert event["details"]["scan_kind"] == "dicom"
    assert event["event_id"].startswith("medical_scan_")

