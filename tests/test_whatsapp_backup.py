from pathlib import Path

from integrations.whatsapp_backup import WhatsAppBackupConnector


DATA_DIR = Path(__file__).parent / "data"


def test_parse_plain_text_chat():
    connector = WhatsAppBackupConnector(chat_name="New Year")
    events = connector.parse(DATA_DIR / "whatsapp_plain.txt")
    assert len(events) == 2
    assert events[0]["actor"] == "Alice"
    assert events[0]["timestamp"] == "2021-01-01T10:00:00"
    assert events[0]["details"]["message"] == "Happy New Year!"
    assert events[1]["details"]["media_omitted"] is True
    assert connector.participants == {"Alice", "Bob"}


def test_parse_json_chat():
    connector = WhatsAppBackupConnector()
    events = connector.parse(DATA_DIR / "whatsapp.json")
    assert len(events) == 2
    assert events[0]["actor"] == "Alice"
    assert events[1]["details"]["media_omitted"] is True
    assert connector.participants == {"Alice", "Bob"}
