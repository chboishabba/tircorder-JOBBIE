"""Read transactions from MoneyManagerEx database."""
import sqlite3
from datetime import datetime
from typing import List

from .base import AccountPlugin
from ..banking import Transaction


class MoneyManagerExPlugin(AccountPlugin):
    """Load transaction rows from the MoneyManagerEx SQLite database."""

    def fetch_transactions(self, db_path: str) -> List[Transaction]:
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        cur.execute(
            "SELECT TRANSDATE, AMOUNT, MEMO FROM CHECKINGACCOUNT_V1"
        )
        rows = cur.fetchall()
        conn.close()
        transactions: List[Transaction] = []
        for date_str, amount, memo in rows:
            try:
                dt = datetime.strptime(date_str, "%Y-%m-%d")
            except ValueError:
                continue
            transactions.append(
                Transaction(
                    date=dt,
                    amount=float(amount),
                    description=memo or "",
                    source_account="checking",
                )
            )
        return transactions
