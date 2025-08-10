"""Placeholder utilities for importing chat histories from LLM interfaces."""
from typing import Dict, List


def load_chat_history(path: str) -> List[Dict]:
    """Load chat transcripts from *path*.

    This function is a placeholder which would parse exported conversations
    from LLM chat interfaces (e.g. ChatGPT, Claude) into timeline events.
    """
    raise NotImplementedError("Chat history integration not yet implemented")
