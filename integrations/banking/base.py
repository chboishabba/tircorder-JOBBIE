from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, Iterable, List, Optional, Sequence, Tuple


@dataclass
class Transaction:
    """Represents a single money movement between accounts."""

    date: datetime
    amount: float
    currency: str = ""
    description: str = ""
    source_account: str = ""
    destination_account: Optional[str] = None
    metadata: Dict[str, str] = field(default_factory=dict)


def transaction_to_event(tx: Transaction) -> Dict:
    """Convert a :class:`Transaction` into a timeline event dictionary."""
    event = {
        "time": tx.date,
        "label": tx.description or "Transaction",
        "amount": tx.amount,
        "currency": tx.currency,
        "source_account": tx.source_account,
        "destination_account": tx.destination_account,
    }
    if tx.metadata:
        event["metadata"] = tx.metadata
    return event


def transactions_to_events(transactions: Iterable[Transaction]) -> List[Dict]:
    """Turn a list of transactions into timeline events."""
    return [transaction_to_event(tx) for tx in transactions]


def link_transactions_to_events(
    transactions: Sequence[Transaction],
    events: Sequence[Dict],
    tolerance: timedelta = timedelta(hours=1),
) -> List[Tuple[Transaction, Optional[Dict]]]:
    """Associate each transaction with a nearby timeline event.

    Parameters
    ----------
    transactions:
        Ordered sequence of transactions.
    events:
        Timeline events sorted by time.
    tolerance:
        Maximum distance between transaction time and event time for them to be
        considered linked.

    Returns
    -------
    list of tuple
        List of ``(transaction, event)`` pairs.  ``event`` will be ``None`` if
        no suitable match is found within the tolerance window.
    """
    linked: List[Tuple[Transaction, Optional[Dict]]] = []
    for tx in transactions:
        match: Optional[Dict] = None
        for ev in events:
            tdiff = abs(ev.get("time") - tx.date)
            if tdiff <= tolerance:
                match = ev
                break
        linked.append((tx, match))
    return linked


class BankingPlugin:
    """Base class for bank statement parsers."""

    def parse_file(self, path: str) -> List[Transaction]:  # pragma: no cover - interface
        """Parse the given file and return a list of transactions."""
        raise NotImplementedError
