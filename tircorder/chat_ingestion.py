"""Chat ingestion workflow utilities."""
from __future__ import annotations

from typing import Any, Dict, List, Optional
import sqlite3

from integrations.chat_history import load_chat_history
from tircorder.chat_storage import upsert_chat_events, DB_PATH


def ingest_chat_history(
    path: str,
    *,
    conn: Optional[sqlite3.Connection] = None,
    db_path: str = DB_PATH,
) -> List[Dict[str, Any]]:
    """Load chat history from *path* and persist the resulting events."""

    events = load_chat_history(path)
    upsert_chat_events(events, conn=conn, db_path=db_path)
    return events
