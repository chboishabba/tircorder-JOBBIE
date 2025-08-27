import json
from pathlib import Path

from integrations.tiktok_backup import TikTokBackupConnector
from tircorder.schemas import validate_story


def _write_json(path: Path, data) -> None:
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(data, fh)


def test_tiktok_backup_connector(tmp_path: Path) -> None:
    videos = {
        "VideoBrowsingHistory": [
            {
                "Date": "2024-05-01T12:00:00Z",
                "Link": "https://tiktok.com/v1",
                "Title": "funny",
            },
            {
                "Date": "bad-date",
                "Link": "https://tiktok.com/v2",
            },
        ]
    }
    comments = {
        "Comments": [
            {
                "Date": "2024-05-02T13:00:00Z",
                "Comment": "nice",
                "Link": "https://tiktok.com/v3",
            },
            {"Comment": "missing date"},
        ]
    }
    messages = {
        "DirectMessages": [
            {
                "Date": "2024-05-03T14:00:00Z",
                "From": "alice",
                "To": "bob",
                "Message": "hi",
            },
            {
                "Date": "2024-05-04T15:00:00Z",
                "Message": "anon",
            },
        ]
    }

    _write_json(tmp_path / "Video Browsing History.json", videos)
    _write_json(tmp_path / "Comments.json", comments)
    _write_json(tmp_path / "Messages.json", messages)

    connector = TikTokBackupConnector(tmp_path)
    events = list(connector.iter_events())

    assert len(events) == 4
    actions = [e["action"] for e in events]
    assert actions.count("watch") == 1
    assert actions.count("comment") == 1
    assert actions.count("message") == 2
    for ev in events:
        validate_story(ev)


def test_tiktok_backup_handles_many_videos(tmp_path: Path) -> None:
    videos = {
        "VideoBrowsingHistory": [
            {
                "Date": "2024-01-01T00:00:00Z",
                "Link": f"https://tiktok.com/v{i}",
            }
            for i in range(100)
        ]
    }
    _write_json(tmp_path / "videos.json", videos)

    connector = TikTokBackupConnector(tmp_path)
    count = sum(1 for _ in connector.iter_video_history())
    assert count == 100
