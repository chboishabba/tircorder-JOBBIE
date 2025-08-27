from pathlib import Path

from integrations.slack_backup import SlackBackupConnector


def test_slack_backup_connector_parses_events():
    export_dir = Path(__file__).parent / "data" / "slack_export"
    connector = SlackBackupConnector(str(export_dir))
    events = connector.load_messages()
    assert len(events) == 4

    # file reference
    file_event = next(e for e in events if e["details"].get("files"))
    file_path = Path(file_event["details"]["files"][0])
    assert file_path.name == "test.txt"
    assert file_path.exists()

    # bot message
    bot_event = next(e for e in events if e["actor"].startswith("bot:"))
    assert bot_event["details"]["channel"] == "general"

    # system message
    sys_event = next(e for e in events if e["actor"] == "system")
    assert sys_event["details"]["channel"] == "general"

    # user message
    user_event = next(
        e
        for e in events
        if e["actor"] == "U123" and e["details"]["text"] == "Hello world"
    )
    assert user_event["details"]["channel"] == "general"
