import datetime as dt

import pytest

from integrations.banking.base import Transaction
from transaction_analysis import find_suspicious_cycles


@pytest.fixture
def cyclic_transactions():
    now = dt.datetime.now()
    return [
        Transaction(date=now, amount=100, source_account="A", destination_account="B"),
        Transaction(date=now, amount=50, source_account="B", destination_account="C"),
        Transaction(date=now, amount=25, source_account="C", destination_account="A"),
    ]


@pytest.fixture
def acyclic_transactions():
    now = dt.datetime.now()
    return [
        Transaction(date=now, amount=100, source_account="A", destination_account="B"),
        Transaction(date=now, amount=50, source_account="B", destination_account="C"),
        Transaction(date=now, amount=25, source_account="C", destination_account="D"),
    ]


def test_detects_cycles(cyclic_transactions):
    result = find_suspicious_cycles(cyclic_transactions)
    assert result["cycles"], "Expected at least one cycle to be detected"


def test_no_cycles_in_acyclic_flow(acyclic_transactions):
    result = find_suspicious_cycles(acyclic_transactions)
    assert result["cycles"] == []
