import json
from pathlib import Path

from tircorder.interfaces.story_exporter import JSONStoryExporter


def test_json_story_exporter_round_trip(tmp_path: Path) -> None:
    events = [{"id": 1, "text": "hello"}, {"id": 2, "text": "world"}]
    exporter = JSONStoryExporter(events)

    output = tmp_path / "events.json"
    exporter.export_to_file(output)

    with open(output, "r", encoding="utf-8") as fh:
        loaded = json.load(fh)

    assert loaded == events
    assert exporter.export_stories() == events
