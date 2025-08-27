import json
from pathlib import Path

import pytest

from integrations.instagram_backup import InstagramBackupConnector


def write_json(path: Path, data: list) -> None:
    path.write_text(json.dumps(data), encoding="utf-8")


def test_instagram_backup_connector_parses_events(tmp_path: Path) -> None:
    posts = [
        {
            "id": "p1",
            "timestamp": "2024-01-01T12:00:00+00:00",
            "caption": "hello",
            "media": "photo.jpg",
        }
    ]
    stories = [
        {
            "id": "s1",
            "timestamp": "2024-01-02T12:00:00+00:00",
            "media": "story.jpg",
        }
    ]
    messages = [
        {
            "id": "m1",
            "timestamp": "2024-01-03T12:00:00+00:00",
            "sender": "alice",
            "text": "hi",
        }
    ]

    write_json(tmp_path / "posts.json", posts)
    write_json(tmp_path / "stories.json", stories)
    write_json(tmp_path / "messages.json", messages)

    connector = InstagramBackupConnector(tmp_path)
    events = connector.load()

    assert len(events) == 3
    assert {e["action"] for e in events} == {"post", "story", "message"}


def test_instagram_backup_connector_missing_fields(tmp_path: Path) -> None:
    posts = [{"id": "p1", "caption": "no timestamp", "media": "p.jpg"}]
    write_json(tmp_path / "posts.json", posts)

    connector = InstagramBackupConnector(tmp_path)
    with pytest.raises(ValueError):
        connector.load()

    posts = [
        {
            "id": "p2",
            "timestamp": "2024-01-01T12:00:00+00:00",
            "caption": "no media",
        }
    ]
    write_json(tmp_path / "posts.json", posts)
    with pytest.raises(ValueError):
        connector.load()
