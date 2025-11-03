"""Utilities for persisting chat history events to the state database."""
from __future__ import annotations

import json
import sqlite3
from typing import Any, Iterable, Mapping, Optional

DB_PATH = "state.db"


def ensure_chat_events_schema(conn: sqlite3.Connection) -> None:
    """Ensure the ``chat_events`` table and indexes exist."""
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS chat_events (
            event_id TEXT PRIMARY KEY,
            timestamp TEXT NOT NULL,
            actor TEXT,
            action TEXT,
            details TEXT
        )
        """
    )
    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_chat_events_timestamp
        ON chat_events(timestamp)
        """
    )
    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_chat_events_actor
        ON chat_events(actor)
        """
    )


def _serialise_details(details: Any) -> Optional[str]:
    if details is None:
        return None
    if isinstance(details, str):
        return details
    return json.dumps(details)


def upsert_chat_events(
    events: Iterable[Mapping[str, Any]],
    *,
    conn: Optional[sqlite3.Connection] = None,
    db_path: str = DB_PATH,
) -> int:
    """Insert or update chat events in the database.

    Parameters
    ----------
    events:
        Iterable of mapping objects containing ``event_id``, ``timestamp``,
        ``actor``, ``action`` and ``details`` fields.
    conn:
        Optional existing database connection. When omitted a new connection is
        created using ``db_path``.
    db_path:
        Path to the SQLite database used when ``conn`` is not provided.

    Returns
    -------
    int
        The number of events written to the database.
    """

    materialised_events = list(events)
    if not materialised_events:
        return 0

    owns_connection = False
    if conn is None:
        conn = sqlite3.connect(db_path)
        owns_connection = True

    try:
        ensure_chat_events_schema(conn)
        rows = []
        for event in materialised_events:
            try:
                event_id = event["event_id"]
                timestamp = event["timestamp"]
            except KeyError as exc:  # pragma: no cover - defensive guard
                raise ValueError("event is missing required fields") from exc

            actor = event.get("actor")
            action = event.get("action")
            details = _serialise_details(event.get("details"))
            rows.append((event_id, timestamp, actor, action, details))

        conn.executemany(
            """
            INSERT INTO chat_events (event_id, timestamp, actor, action, details)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(event_id) DO UPDATE SET
                timestamp=excluded.timestamp,
                actor=excluded.actor,
                action=excluded.action,
                details=excluded.details
            """,
            rows,
        )
        conn.commit()
    finally:
        if owns_connection:
            conn.close()

    return len(rows)
