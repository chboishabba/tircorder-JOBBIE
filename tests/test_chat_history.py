"""Tests for the ChatGPT chat history integration."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict, List
import sys
import types

import pytest

stub_sync_module = types.ModuleType("reverse_engineered_chatgpt.re_gpt.sync_chatgpt")
stub_sync_module.SyncChatGPT = object  # type: ignore[attr-defined]
stub_regpt_module = types.ModuleType("reverse_engineered_chatgpt.re_gpt")
stub_regpt_module.sync_chatgpt = stub_sync_module  # type: ignore[attr-defined]
stub_package = types.ModuleType("reverse_engineered_chatgpt")
stub_package.re_gpt = stub_regpt_module  # type: ignore[attr-defined]

sys.modules.setdefault("reverse_engineered_chatgpt", stub_package)
sys.modules.setdefault("reverse_engineered_chatgpt.re_gpt", stub_regpt_module)
sys.modules.setdefault(
    "reverse_engineered_chatgpt.re_gpt.sync_chatgpt", stub_sync_module
)

from integrations import chat_history


class DummyConversation:
    """Simple stand-in for :class:`SyncConversation`."""

    def __init__(self, payload: Dict) -> None:
        self._payload = payload

    def fetch_chat(self) -> Dict:
        return self._payload


class DummyClient:
    """Simple stand-in for :class:`SyncChatGPT`."""

    def __init__(self, session_token: str, conversations: Dict[str, Dict]):
        self.session_token = session_token
        self._conversations = conversations

    def list_all_conversations(self) -> List[str]:
        return list(self._conversations)

    def get_conversation(self, conversation_id: str) -> DummyConversation:
        return DummyConversation(self._conversations[conversation_id])


@pytest.fixture
def sample_payload() -> Dict[str, Dict]:
    user_time = datetime(2024, 5, 10, 12, 0, tzinfo=timezone.utc).timestamp()
    assistant_time = "2024-05-10T12:01:00+00:00"
    return {
        "conv-1": {
            "mapping": {
                "node-user": {
                    "id": "node-user",
                    "parent": None,
                    "message": {
                        "id": "msg-user",
                        "create_time": user_time,
                        "author": {"role": "user"},
                        "content": {"parts": ["Hello there!"]},
                    },
                },
                "node-assistant": {
                    "id": "node-assistant",
                    "parent": "node-user",
                    "message": {
                        "id": "msg-assistant",
                        "create_time": assistant_time,
                        "author": {"role": "assistant"},
                        "content": {"parts": ["Hi, how can I help you today?"]},
                    },
                },
            }
        }
    }


def test_load_chat_history_monkeypatched(monkeypatch, tmp_path, sample_payload):
    token_file = tmp_path / "session_token.txt"
    token_file.write_text("dummy-token", encoding="utf-8")

    def factory(session_token: str) -> DummyClient:
        assert session_token == "dummy-token"
        return DummyClient(session_token, sample_payload)

    monkeypatch.setattr(chat_history, "SyncChatGPT", factory)

    events = chat_history.load_chat_history(str(token_file))

    assert len(events) == 2
    first, second = events

    assert first["event_id"] == "chatgpt_msg-user"
    assert first["actor"] == "user"
    assert first["action"] == "chat_message"
    assert first["details"]["conversation_id"] == "conv-1"
    assert first["details"]["parent_id"] is None
    assert first["details"]["text"] == "Hello there!"

    expected_first_timestamp = datetime.fromtimestamp(
        sample_payload["conv-1"]["mapping"]["node-user"]["message"]["create_time"],
        tz=timezone.utc,
    ).isoformat()
    assert first["timestamp"] == expected_first_timestamp

    assert second["actor"] == "assistant"
    assert second["details"]["parent_id"] == "node-user"
    assert second["details"]["text"] == "Hi, how can I help you today?"
    assert second["timestamp"] == "2024-05-10T12:01:00+00:00"


def test_load_chat_history_without_token(tmp_path):
    empty_token = tmp_path / "token.txt"
    empty_token.write_text("\n", encoding="utf-8")

    events = chat_history.load_chat_history(str(empty_token))

    assert events == []
