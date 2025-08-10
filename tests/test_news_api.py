from datetime import date
import requests

from integrations.news_api import BASE_URL, search_news


class DummyResponse:
    def __init__(self, data):
        self._data = data

    def raise_for_status(self) -> None:  # pragma: no cover - no exception
        return None

    def json(self):
        return self._data


def test_search_news_success(monkeypatch):
    captured = {}

    def fake_get(url, params=None, timeout=0):
        captured["url"] = url
        captured["params"] = params
        return DummyResponse({"articles": [{"title": "headline"}]})

    monkeypatch.setattr(requests, "get", fake_get)

    result = search_news("keyword", date(2024, 5, 1), "KEY", page_size=5)

    assert result == [{"title": "headline"}]
    assert captured["url"] == BASE_URL
    assert captured["params"]["from"] == "2024-05-01"
    assert captured["params"]["to"] == "2024-05-01"
    assert captured["params"]["q"] == "keyword"
    assert captured["params"]["pageSize"] == 5
    assert captured["params"]["apiKey"] == "KEY"
    assert captured["params"]["language"] == "en"
    assert captured["params"]["sortBy"] == "relevancy"


def test_search_news_failure(monkeypatch):
    def fake_get(*args, **kwargs):
        raise requests.RequestException("boom")

    monkeypatch.setattr(requests, "get", fake_get)

    result = search_news("anything", date(2024, 5, 1), "KEY")

    assert result == []
