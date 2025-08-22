"""Abstract visualiser interface and Bevy implementation."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any
import json


class Visualiser(ABC):
    """Base class for visualisers."""

    @abstractmethod
    def visualise(self, data: Any) -> None:
        """Render *data* to a front-end.

        Parameters
        ----------
        data:
            JSON serialisable structure describing the render.
        """


class BevyVisualiser(Visualiser):
    """Forward JSON data to a Bevy front-end."""

    def visualise(self, data: Any) -> None:  # noqa: D401
        message = json.dumps(data)
        self.send_to_bevy(message)

    def send_to_bevy(self, message: str) -> None:
        """Placeholder for communication with Bevy."""
        raise NotImplementedError("Implement Bevy communication")
