"""Parser for OFX (Open Financial Exchange) statements."""
from typing import List

from .base import BankingPlugin, Transaction


class OFXBankingPlugin(BankingPlugin):
    """Parse OFX files using the ``ofxparse`` library."""

    def parse_file(self, path: str) -> List[Transaction]:
        try:
            from ofxparse import OfxParser  # type: ignore
        except Exception as exc:  # pragma: no cover - optional dependency
            raise RuntimeError("ofxparse library is required for OFX support") from exc

        with open(path, "rb") as fh:
            ofx = OfxParser.parse(fh)

        transactions: List[Transaction] = []
        for account in ofx.accounts:
            for tx in account.statement.transactions:
                transactions.append(
                    Transaction(
                        date=tx.date,
                        amount=tx.amount,
                        currency=account.statement.currency or "",
                        description=tx.memo or "",
                        source_account=account.account_id,
                    )
                )
        return transactions
