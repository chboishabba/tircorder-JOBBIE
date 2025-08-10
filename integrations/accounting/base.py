"""Base classes for account management integrations."""
from typing import List

from ..banking import Transaction


class AccountPlugin:
    """Interface for importing transactions from account managers."""

    def fetch_transactions(self, *args, **kwargs) -> List[Transaction]:  # pragma: no cover - interface
        """Return a list of :class:`~integrations.banking.Transaction` objects."""
        raise NotImplementedError
