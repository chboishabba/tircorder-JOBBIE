"""Adapter for importing Quicken data via QIF exports."""
from typing import List

from .base import AccountPlugin
from ..banking import Transaction
from ..banking.qif_plugin import QIFPlugin


class QuickenPlugin(AccountPlugin):
    """Leverage the existing QIF parser to read Quicken statements."""

    def __init__(self) -> None:
        self._parser = QIFPlugin()

    def fetch_transactions(self, path: str) -> List[Transaction]:
        return self._parser.parse_file(path)
