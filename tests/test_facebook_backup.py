import json
from datetime import datetime, timezone

from integrations.facebook_backup import FacebookBackupConnector


def _write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(data, fh)


def test_parse_posts(tmp_path):
    root = tmp_path / "fb"
    media = root / "media"
    media.mkdir(parents=True)
    (media / "photo.jpg").write_bytes(b"test")
    posts = {
        "posts": [
            {
                "timestamp": 1609459200,
                "data": [{"post": "Happy New Year!"}],
                "attachments": [{"data": [{"media": {"uri": "media/photo.jpg"}}]}],
            }
        ]
    }
    _write_json(root / "posts" / "your_posts.json", posts)
    connector = FacebookBackupConnector(str(root))
    events = list(connector.iter_posts())
    assert len(events) == 1
    event = events[0]
    assert event["action"] == "post"
    assert event["details"]["text"] == "Happy New Year!"
    assert event["details"]["media"][0].endswith("media/photo.jpg")
    # ensure timestamp parsed correctly
    ts = datetime.fromisoformat(event["timestamp"])
    assert ts == datetime(2021, 1, 1, tzinfo=timezone.utc)


def test_parse_messages(tmp_path):
    root = tmp_path / "fb"
    photos = root / "messages" / "inbox" / "thread" / "photos"
    photos.mkdir(parents=True, exist_ok=True)
    (photos / "img.jpg").write_bytes(b"test")
    messages = {
        "messages": [
            {
                "timestamp_ms": 1609459200000,
                "sender_name": "Alice",
                "content": "Hi",
                "photos": [{"uri": "messages/inbox/thread/photos/img.jpg"}],
            }
        ]
    }
    _write_json(root / "messages" / "inbox" / "thread" / "message_1.json", messages)
    connector = FacebookBackupConnector(str(root))
    events = list(connector.iter_messages())
    assert len(events) == 1
    event = events[0]
    assert event["actor"] == "Alice"
    assert event["details"]["text"] == "Hi"
    assert event["details"]["thread"] == "thread"
    assert event["details"]["media"][0].endswith("messages/inbox/thread/photos/img.jpg")
