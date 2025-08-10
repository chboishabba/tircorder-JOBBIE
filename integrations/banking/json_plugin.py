"""Parser for JSON-based bank statement exports."""
from datetime import datetime
from typing import List
import json

from .base import BankingPlugin, Transaction


class JSONBankingPlugin(BankingPlugin):
    """Parse JSON files with a list of transactions."""

    def parse_file(self, path: str) -> List[Transaction]:
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
        items = data.get("transactions") if isinstance(data, dict) else data
        transactions: List[Transaction] = []
        for row in items:
            try:
                date = datetime.fromisoformat(row.get("date", ""))
            except ValueError:
                continue
            tx = Transaction(
                date=date,
                amount=float(row.get("amount", 0)),
                currency=row.get("currency", ""),
                description=row.get("description", ""),
                source_account=row.get("source_account", ""),
                destination_account=row.get("destination_account") or None,
            )
            transactions.append(tx)
        return transactions
