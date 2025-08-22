"""Tools for exporting stories to various formats."""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from typing import Any, Dict, List


class StoryExporter(ABC):
    """Abstract base class for exporting story events."""

    @abstractmethod
    def export_stories(self) -> List[Dict[str, Any]]:
        """Return a list of story events."""

    @abstractmethod
    def export_to_file(self, filepath: str) -> None:
        """Export the stories to *filepath*."""


class JSONStoryExporter(StoryExporter):
    """Serialise story events to a JSON file."""

    def __init__(self, events: List[Dict[str, Any]]):
        """Initialise the exporter with *events*."""
        self.events = events

    def export_stories(self) -> List[Dict[str, Any]]:
        """Return the stored events."""
        return self.events

    def export_to_file(self, filepath: str) -> None:
        """Write events as UTF-8 encoded JSON to *filepath*."""
        with open(filepath, "w", encoding="utf-8") as fh:
            json.dump(self.export_stories(), fh, ensure_ascii=False, indent=2)
