import pytest

from integrations.medical import MyHealthRecordConnector


def test_authenticate_stores_token():
    connector = MyHealthRecordConnector()
    connector.authenticate("secret")
    assert connector.token == "secret"


def test_fetch_records_not_implemented():
    connector = MyHealthRecordConnector()
    with pytest.raises(NotImplementedError):
        connector.fetch_records("patient")
