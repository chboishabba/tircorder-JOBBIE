from pathlib import Path
from typing import List, Dict

from integrations.linkedin_backup import LinkedInBackupConnector
from tircorder.schemas import validate_story


def create_sample_export(base: Path) -> None:
    base.mkdir(parents=True, exist_ok=True)
    (base / "messages.csv").write_text(
        """Date,From,To,Message
2024-06-01 10:00:00 +0000,Alice,Bob,Hello Bob
2024-06-01 11:00:00 +0100,Bob,Alice,
""",
        encoding="utf-8",
    )
    (base / "profile_updates.json").write_text(
        """[
  {"timestamp": "2024-06-02T09:00:00Z", "update": "Changed headline"},
  {"timestamp": "2024-06-03 15:30:00 +0200", "update": "Updated location", "location": "Paris"}
]
""",
        encoding="utf-8",
    )
    (base / "posts.json").write_text(
        """[
  {"timestamp": "2024-06-04T12:00:00", "text": "New post!"},
  {"timestamp": "2024-06-05T08:00:00-0500", "text": "Another post", "url": "https://example.com/post"}
]
""",
        encoding="utf-8",
    )


def test_linkedin_backup_connector_parses_exports(tmp_path: Path) -> None:
    export_dir = tmp_path / "linkedin"
    create_sample_export(export_dir)

    connector = LinkedInBackupConnector(export_dir)
    events: List[Dict] = connector.load_events()

    assert len(events) == 6
    actions = {e["action"] for e in events}
    assert actions == {"message", "profile_update", "post"}

    # time zone normalization: second message +0100 -> 10:00 UTC
    msg = [e for e in events if e["action"] == "message"]
    second = msg[1]
    assert second["timestamp"].startswith("2024-06-01T10:00:00")
    assert second["timestamp"].endswith("+00:00")
    assert second["details"]["text"] == ""

    for event in events:
        validate_story(event)
