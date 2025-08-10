"""Parser for QIF (Quicken Interchange Format) files."""
from typing import List

from .base import BankingPlugin, Transaction


class QIFBankingPlugin(BankingPlugin):
    """Parse QIF files using the ``qifparse`` library."""

    def parse_file(self, path: str) -> List[Transaction]:
        try:
            import qifparse.parser as qifparser  # type: ignore
        except Exception as exc:  # pragma: no cover - optional dependency
            raise RuntimeError("qifparse library is required for QIF support") from exc

        with open(path, "r", encoding="utf-8") as fh:
            qif = qifparser.QifParser.parse(fh)

        transactions: List[Transaction] = []
        for tx in qif.get_transactions():
            transactions.append(
                Transaction(
                    date=tx.date,
                    amount=tx.amount,
                    currency="",
                    description=tx.memo or "",
                    source_account=tx.account or "",
                )
            )
        return transactions
