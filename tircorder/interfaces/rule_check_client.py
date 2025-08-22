"""Clients for checking event compliance via Sensiblaw."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict

import requests


class RuleCheckClient(ABC):
    """Abstract client for verifying events with Sensiblaw."""

    @abstractmethod
    def check_event_with_sensiblaw(self, event: Dict[str, Any]) -> bool:
        """Return whether ``event`` is compliant according to Sensiblaw."""


class HTTPRuleCheckClient(RuleCheckClient):
    """HTTP implementation of :class:`RuleCheckClient`."""

    def __init__(self, base_url: str, timeout: float = 5.0) -> None:
        """Initialize client with API ``base_url`` and request ``timeout``."""

        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def check_event_with_sensiblaw(self, event: Dict[str, Any]) -> bool:
        """POST ``event`` to the Sensiblaw API and return compliance result."""

        url = f"{self.base_url}/rules/check"
        response = requests.post(url, json={"event": event}, timeout=self.timeout)
        response.raise_for_status()
        data = response.json()
        return bool(data.get("compliant"))
