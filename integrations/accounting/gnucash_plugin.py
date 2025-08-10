"""Import transactions from a GnuCash book file."""
from datetime import datetime
from typing import List, Optional

from piecash import open_book

from .base import AccountPlugin
from ..banking import Transaction


class GnuCashPlugin(AccountPlugin):
    """Read transactions from a local GnuCash file using :mod:`piecash`."""

    def fetch_transactions(
        self, path: str, start: Optional[datetime] = None, end: Optional[datetime] = None
    ) -> List[Transaction]:
        with open_book(path) as book:
            transactions: List[Transaction] = []
            for tx in book.transactions:
                if start and tx.post_date < start:
                    continue
                if end and tx.post_date > end:
                    continue
                for split in tx.splits:
                    transactions.append(
                        Transaction(
                            date=tx.post_date,
                            amount=float(split.value),
                            currency=split.account.commodity.mnemonic,
                            description=tx.description or "",
                            source_account=split.account.fullname,
                        )
                    )
        return transactions
