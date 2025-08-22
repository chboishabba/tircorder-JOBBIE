import importlib.util
import json
import sys
from pathlib import Path

MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "tircorder"
    / "interfaces"
    / "story_exporter.py"
)

spec = importlib.util.spec_from_file_location("story_exporter", MODULE_PATH)
story_exporter = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = story_exporter
spec.loader.exec_module(story_exporter)
JSONStoryExporter = story_exporter.JSONStoryExporter


def test_json_story_exporter_round_trip(tmp_path: Path) -> None:
    events = [{"id": 1, "text": "hello"}, {"id": 2, "text": "world"}]
    exporter = JSONStoryExporter(events)

    output = tmp_path / "events.json"
    exporter.export_to_file(output)

    with open(output, "r", encoding="utf-8") as fh:
        loaded = json.load(fh)

    assert loaded == events
    assert exporter.export_stories() == events
