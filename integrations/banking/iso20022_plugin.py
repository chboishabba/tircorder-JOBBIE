"""Parser for ISO 20022 (camt.053) XML statements."""
from datetime import datetime
from typing import List
import xml.etree.ElementTree as ET

from .base import BankingPlugin, Transaction


class ISO20022BankingPlugin(BankingPlugin):
    """Parse ISO 20022 XML files for basic transaction data."""

    def parse_file(self, path: str) -> List[Transaction]:
        tree = ET.parse(path)
        root = tree.getroot()
        ns = {"ns": root.tag.split("}")[0].strip("{")}
        tx_nodes = root.findall(
            ".//ns:Ntry/ns:NtryDtls/ns:TxDtls", ns
        )  # typical camt.053 path
        transactions: List[Transaction] = []
        for node in tx_nodes:
            amt_node = node.find("ns:Amt", ns)
            date_node = node.find("ns:BookgDt/ns:Dt", ns)
            descr_node = node.find("ns:RmtInf/ns:Ustrd", ns)
            if amt_node is None or date_node is None:
                continue
            currency = amt_node.attrib.get("Ccy", "")
            amount = float(amt_node.text or 0)
            date = datetime.fromisoformat(date_node.text)
            description = descr_node.text if descr_node is not None else ""
            transactions.append(
                Transaction(
                    date=date,
                    amount=amount,
                    currency=currency,
                    description=description,
                )
            )
        return transactions
