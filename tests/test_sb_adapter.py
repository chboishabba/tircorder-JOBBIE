import json
from pathlib import Path

from tircorder.sb_adapter import build_execution_envelope


FIXTURE_DIR = Path(__file__).parent / "fixtures"


def _load_fixture() -> dict:
    return json.loads((FIXTURE_DIR / "whisperx_sample.json").read_text(encoding="utf-8"))


def test_execution_envelope_has_provenance_and_audio_hash():
    transcript = _load_fixture()
    audio_path = FIXTURE_DIR / "whisperx_sample.wav"

    payload = build_execution_envelope(
        transcript,
        source="whisperx_webui",
        audio_path=audio_path,
        adapter_label="tircorder_whisperx_webui_v1",
    )

    envelope = payload["execution_envelope"]
    assert envelope["provenance"]["adapter"] == "tircorder_whisperx_webui_v1"
    assert envelope["provenance"]["transcript_hash"]
    assert envelope["audio_hash"]
    assert envelope["segment_count"] == len(transcript["segments"])


def test_segment_confidence_retained():
    transcript = _load_fixture()
    payload = build_execution_envelope(transcript, source="whisperx_webui")
    segments = payload["segment_events"]

    assert segments[0]["data"]["confidence"] == transcript["segments"][0]["confidence"]
    assert segments[1]["data"]["confidence"] == transcript["segments"][1]["confidence"]


def test_no_semantic_labels_emitted():
    transcript = _load_fixture()
    payload = build_execution_envelope(transcript, source="whisperx_webui")

    forbidden = {"summary", "sentiment", "intent", "emotion", "diagnosis"}

    envelope = payload["execution_envelope"]
    assert forbidden.isdisjoint(envelope.keys())

    for segment in payload["segment_events"]:
        keys = set(segment["data"].keys())
        assert forbidden.isdisjoint(keys)
        assert keys.issuperset({"text", "start", "end", "confidence", "provenance"})
