"""Parse transactions from KMyMoney XML files."""
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import List

from .base import AccountPlugin
from ..banking import Transaction


class KMyMoneyPlugin(AccountPlugin):
    """Load transactions from the ``.kmy`` XML format used by KMyMoney."""

    def fetch_transactions(self, path: str) -> List[Transaction]:
        tree = ET.parse(path)
        root = tree.getroot()
        ns = {"kmm": root.tag.split('}')[0].strip('{')} if root.tag.startswith('{') else {}
        transactions: List[Transaction] = []
        for tx in root.findall('.//kmm:TRANSACTION', ns):
            date_str = tx.get('postdate')
            if not date_str:
                continue
            try:
                dt = datetime.strptime(date_str, '%Y-%m-%d')
            except ValueError:
                continue
            memo = tx.get('memo', '')
            for split in tx.findall('kmm:SPLITS/kmm:SPLIT', ns):
                amount = float(split.get('value', '0').replace(',', '.'))
                account = split.get('account', '')
                transactions.append(
                    Transaction(
                        date=dt,
                        amount=amount,
                        description=memo,
                        source_account=account,
                    )
                )
        return transactions
