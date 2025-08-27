"""Tests for GoogleTakeoutConnector."""

from __future__ import annotations

import json
from pathlib import Path

from integrations.google_takeout import GoogleTakeoutConnector


def _write_json_lines(path: Path, items: list) -> None:
    with open(path, "w", encoding="utf-8") as fh:
        for obj in items:
            fh.write(json.dumps(obj) + "\n")
        fh.write("not json\n")


def _create_takeout(tmp_path: Path) -> Path:
    gmail_dir = tmp_path / "Gmail"
    gmail_dir.mkdir()
    gmail_file = gmail_dir / "All mail.json"
    gmail_items = [
        {
            "id": "1",
            "timestamp": "2024-01-02T03:04:05Z",
            "from": "alice@example.com",
            "subject": "Hello",
            "snippet": "Hi",
        },
        {"id": "2", "timestamp": "bad"},
    ]
    _write_json_lines(gmail_file, gmail_items)

    drive_dir = tmp_path / "Drive"
    drive_dir.mkdir()
    drive_file = drive_dir / "Activity.json"
    drive_items = [
        {
            "time": "2024-01-02T04:00:00Z",
            "actor": "user",
            "action": "edit",
            "target": "doc1",
        }
    ]
    with open(drive_file, "w", encoding="utf-8") as fh:
        json.dump(drive_items, fh)

    photos_dir = tmp_path / "Google Photos"
    photos_dir.mkdir()
    photos_file = photos_dir / "metadata.json"
    photos_items = [{"creationTime": "2024-01-01T00:00:00Z", "fileName": "img1.jpg"}]
    with open(photos_file, "w", encoding="utf-8") as fh:
        json.dump(photos_items, fh)

    return tmp_path


def test_google_takeout_connector(tmp_path: Path) -> None:
    base = _create_takeout(tmp_path)
    connector = GoogleTakeoutConnector(base)
    events = list(connector.iter_events())
    assert len(events) == 3

    email = next(e for e in events if e["action"] == "email")
    assert email["details"]["subject"] == "Hello"

    drive = next(e for e in events if e["action"] == "edit")
    assert drive["details"]["target"] == "doc1"

    photo = next(e for e in events if e["action"] == "photo")
    assert photo["details"]["file_name"] == "img1.jpg"
