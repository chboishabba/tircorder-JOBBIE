import importlib.util
import requests

spec = importlib.util.spec_from_file_location(
    "rule_check_client", "tircorder/interfaces/rule_check_client.py"
)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
HTTPRuleCheckClient = module.HTTPRuleCheckClient


class DummyResponse:
    def __init__(self, data):
        self._data = data

    def raise_for_status(self):  # pragma: no cover - no error expected
        return None

    def json(self):
        return self._data


def test_http_rule_check_client(monkeypatch):
    captured = {}

    def fake_post(url, json=None, timeout=0):
        captured["url"] = url
        captured["json"] = json
        return DummyResponse({"compliant": True})

    monkeypatch.setattr(requests, "post", fake_post)

    client = HTTPRuleCheckClient("http://api")
    event = {"id": 1}
    result = client.check_event_with_sensiblaw(event)

    assert result is True
    assert captured["url"] == "http://api/rules/check"
    assert captured["json"] == {"event": event}
