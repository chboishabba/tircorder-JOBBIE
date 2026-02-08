from datetime import datetime, timezone

from integrations.medical import DoctorNotesFolderConnector


def test_doctor_notes_meta_only_by_default(tmp_path):
    notes_dir = tmp_path / "notes"
    notes_dir.mkdir()
    path = notes_dir / "20260202_visit_note.txt"
    path.write_text("Patient reports pain.", encoding="utf-8")

    collected_at = datetime(2026, 2, 8, 12, 0, 0, tzinfo=timezone.utc)
    connector = DoctorNotesFolderConnector(notes_dir)
    events = connector.load(collected_at=collected_at)

    assert len(events) == 1
    event = events[0]
    assert event["timestamp"] == "2026-02-02T00:00:00+00:00"
    assert "text" not in event["details"]


def test_doctor_notes_can_include_text_with_truncation(tmp_path):
    notes_dir = tmp_path / "notes"
    notes_dir.mkdir()
    path = notes_dir / "2026-02-03_long_note.md"
    path.write_text("x" * 100, encoding="utf-8")

    connector = DoctorNotesFolderConnector(notes_dir, include_text=True, max_text_bytes=10)
    events = connector.load(collected_at=datetime(2026, 2, 8, tzinfo=timezone.utc))

    assert len(events) == 1
    details = events[0]["details"]
    assert details["text_truncated"] is True
    assert len(details["text"].encode("utf-8")) <= 10

