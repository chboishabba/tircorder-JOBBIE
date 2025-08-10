"""Integration with the Firefly-III personal finance manager."""
from datetime import datetime
from typing import List

import requests

from .base import AccountPlugin
from ..banking import Transaction


class FireflyIIIPlugin(AccountPlugin):
    """Fetch transactions from a Firefly-III instance using its REST API."""

    def __init__(self, base_url: str, token: str) -> None:
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        self.session.headers.update({"Authorization": f"Bearer {token}"})

    def fetch_transactions(self, start: datetime, end: datetime) -> List[Transaction]:
        params = {"start": start.date().isoformat(), "end": end.date().isoformat()}
        url = f"{self.base_url}/api/v1/transactions"
        resp = self.session.get(url, params=params, timeout=30)
        resp.raise_for_status()
        payload = resp.json()
        transactions: List[Transaction] = []
        for item in payload.get("data", []):
            attrs = item.get("attributes", {})
            for tx in attrs.get("transactions", []):
                try:
                    dt = datetime.fromisoformat(tx["date"])
                    amount = float(tx["amount"])
                except (KeyError, ValueError):
                    continue
                transactions.append(
                    Transaction(
                        date=dt,
                        amount=amount,
                        currency=tx.get("currency_code", ""),
                        description=tx.get("description", ""),
                        source_account=tx.get("source_name", ""),
                        destination_account=tx.get("destination_name"),
                    )
                )
        return transactions
