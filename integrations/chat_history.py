"""Utilities for importing ChatGPT conversation history."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Sequence

from reverse_engineered_chatgpt.re_gpt.sync_chatgpt import SyncChatGPT

from tircorder.schemas import validate_story


def _coerce_timestamp(value: object) -> Optional[str]:
    """Convert ``value`` into an ISO 8601 timestamp string."""

    if value is None:
        return None
    if isinstance(value, (int, float)):
        return datetime.fromtimestamp(float(value), tz=timezone.utc).isoformat()
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00")).isoformat()
        except ValueError:
            try:
                return datetime.fromtimestamp(float(value), tz=timezone.utc).isoformat()
            except (TypeError, ValueError):
                return None
    return None


def _message_text(parts: Sequence[object]) -> str:
    """Join message ``parts`` into a string suitable for story details."""

    return "\n".join(str(part) for part in parts if part)


def load_chat_history(path: str) -> List[Dict]:
    """Load ChatGPT transcripts using the session token stored at ``path``."""

    session_token = Path(path).read_text(encoding="utf-8").strip()
    if not session_token:
        return []

    client = SyncChatGPT(session_token=session_token)
    events: List[Dict] = []

    for conversation_id in client.list_all_conversations():
        if isinstance(conversation_id, dict):
            conversation_id = conversation_id.get("id") or conversation_id.get(
                "conversation_id"
            )
        if not conversation_id:
            continue

        getter = getattr(client, "get_conversation", None)
        if getter is None:
            getter = getattr(client, "conversation", None)
        if getter is None:
            raise AttributeError("SyncChatGPT client does not expose conversation access")
        conversation = getter(conversation_id)
        chat_payload = conversation.fetch_chat()
        mapping = chat_payload.get("mapping", {}) if isinstance(chat_payload, dict) else {}

        for node in mapping.values():
            if not isinstance(node, dict):
                continue
            message = node.get("message")
            if not isinstance(message, dict):
                continue

            message_id = message.get("id") or node.get("id")
            timestamp = _coerce_timestamp(
                message.get("create_time") or message.get("update_time")
            )
            if not message_id or not timestamp:
                continue

            author = message.get("author", {})
            role = author.get("role") if isinstance(author, dict) else None
            actor = "user" if role == "user" else "assistant"

            content = message.get("content", {})
            if isinstance(content, dict):
                parts = content.get("parts") or []
                if isinstance(parts, (list, tuple)):
                    parts = list(parts)
                elif parts:
                    parts = [parts]
                else:
                    parts = []
            else:
                parts = [content]
            text = _message_text(parts)

            event = {
                "event_id": f"chatgpt_{message_id}",
                "timestamp": timestamp,
                "actor": actor,
                "action": "chat_message",
                "details": {
                    "conversation_id": conversation_id,
                    "message_id": message_id,
                    "parent_id": node.get("parent"),
                    "text": text,
                },
            }
            validate_story(event)
            events.append(event)

    return events
