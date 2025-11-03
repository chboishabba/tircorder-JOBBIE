import json
import sqlite3

import pytest

from tircorder.chat_storage import ensure_chat_events_schema, upsert_chat_events
from tircorder.chat_ingestion import ingest_chat_history


@pytest.fixture()
def memory_conn():
    conn = sqlite3.connect(":memory:")
    try:
        yield conn
    finally:
        conn.close()


def test_ensure_chat_events_schema_creates_table_and_indexes(memory_conn):
    ensure_chat_events_schema(memory_conn)

    columns = {
        column[1]: column[2]
        for column in memory_conn.execute("PRAGMA table_info(chat_events)").fetchall()
    }
    assert columns == {
        "event_id": "TEXT",
        "timestamp": "TEXT",
        "actor": "TEXT",
        "action": "TEXT",
        "details": "TEXT",
    }

    indexes = {
        row[1] for row in memory_conn.execute("PRAGMA index_list(chat_events)").fetchall()
    }
    assert "idx_chat_events_timestamp" in indexes
    assert "idx_chat_events_actor" in indexes


def test_upsert_chat_events_inserts_and_updates(memory_conn):
    event = {
        "event_id": "evt-1",
        "timestamp": "2024-05-01T12:00:00",
        "actor": "Alice",
        "action": "message",
        "details": {"text": "Hello"},
    }

    inserted = upsert_chat_events([event], conn=memory_conn)
    assert inserted == 1

    row = memory_conn.execute(
        "SELECT event_id, timestamp, actor, action, details FROM chat_events"
    ).fetchone()
    assert row == (
        "evt-1",
        "2024-05-01T12:00:00",
        "Alice",
        "message",
        json.dumps({"text": "Hello"}),
    )

    updated_event = {
        "event_id": "evt-1",
        "timestamp": "2024-05-01T12:05:00",
        "actor": "Alice",
        "action": "edit",
        "details": {"text": "Hello again"},
    }

    updated = upsert_chat_events([updated_event], conn=memory_conn)
    assert updated == 1

    row = memory_conn.execute(
        "SELECT event_id, timestamp, actor, action, details FROM chat_events"
    ).fetchone()
    assert row == (
        "evt-1",
        "2024-05-01T12:05:00",
        "Alice",
        "edit",
        json.dumps({"text": "Hello again"}),
    )


def test_ingest_chat_history_persists_events(monkeypatch, memory_conn):
    events = [
        {
            "event_id": "evt-2",
            "timestamp": "2024-05-02T15:30:00",
            "actor": "Bob",
            "action": "message",
            "details": "Hi there",
        }
    ]

    monkeypatch.setattr(
        "tircorder.chat_ingestion.load_chat_history", lambda path: events
    )

    stored_events = ingest_chat_history("/tmp/mock", conn=memory_conn)
    assert stored_events == events

    row = memory_conn.execute(
        "SELECT event_id, timestamp, actor, action, details FROM chat_events"
    ).fetchone()
    assert row == ("evt-2", "2024-05-02T15:30:00", "Bob", "message", "Hi there")
