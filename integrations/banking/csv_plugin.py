"""Parser for simple CSV bank statements."""
from datetime import datetime
from typing import List
import csv

from .base import BankingPlugin, Transaction


class CSVBankingPlugin(BankingPlugin):
    """Parse CSV files with columns like date, amount, description, etc."""

    def parse_file(self, path: str) -> List[Transaction]:
        transactions: List[Transaction] = []
        with open(path, newline="", encoding="utf-8") as fh:
            reader = csv.DictReader(fh)
            for row in reader:
                try:
                    date = datetime.fromisoformat(row.get("date", ""))
                except ValueError:
                    continue
                amount = float(row.get("amount", 0))
                tx = Transaction(
                    date=date,
                    amount=amount,
                    currency=row.get("currency", ""),
                    description=row.get("description", ""),
                    source_account=row.get("source_account", ""),
                    destination_account=row.get("destination_account") or None,
                )
                transactions.append(tx)
        return transactions
