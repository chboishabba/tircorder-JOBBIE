import json
from pathlib import Path

from tircorder.sb_adapter import (
    build_browser_assist_session,
    build_execution_envelope,
    write_execution_envelope,
)


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


def test_write_execution_envelope_creates_parent_and_roundtrips(tmp_path):
    payload = {"execution_envelope": {"id": "x"}, "segment_events": []}
    target = tmp_path / "nested" / "envelope.json"

    written = write_execution_envelope(target, payload)

    assert written == target
    assert written.exists()
    assert json.loads(written.read_text(encoding="utf-8")) == payload


def test_envelope_id_changes_with_audio_hash(tmp_path):
    transcript = {
        "text": "hi",
        "language": "en",
        "segments": [{"text": "a", "start": 0, "end": 1}],
    }
    audio_a = tmp_path / "a.wav"
    audio_b = tmp_path / "b.wav"
    audio_a.write_bytes(b"aaa")
    audio_b.write_bytes(b"bbb")

    payload_a = build_execution_envelope(transcript, source="whisperx_webui", audio_path=audio_a)
    payload_b = build_execution_envelope(transcript, source="whisperx_webui", audio_path=audio_b)

    env_a = payload_a["execution_envelope"]
    env_b = payload_b["execution_envelope"]
    assert env_a["audio_hash"] != env_b["audio_hash"]
    assert env_a["id"] != env_b["id"]


def test_segment_key_filtering_and_skips_non_mapping_segments():
    transcript = {
        "segments": [
            {"text": "a", "start": 0, "end": 1, "confidence": 0.5, "extra": "x"},
            "oops",
        ]
    }
    payload = build_execution_envelope(transcript, segment_keys=("text", "start"))
    segments = payload["segment_events"]

    assert len(segments) == 1
    data = segments[0]["data"]
    assert set(data.keys()).issuperset({"text", "start", "provenance"})
    assert "end" not in data
    assert "confidence" not in data
    assert "extra" not in data


def test_browser_assist_session_hashes_page_fields_and_keeps_bounded_preview():
    payload = build_browser_assist_session(
        session_id="browser-assist-1",
        task_label="find discussed item on page",
        started_at="2026-06-04T00:00:00Z",
        ended_at="2026-06-04T00:01:00Z",
        browser="chrome",
        page_url="https://example.test/private?q=secret",
        page_title="Private Page Title",
        text_preview="alpha beta gamma delta",
        openrecall_entry_refs=["openrecall.entry:7"],
        playwright_snapshot_refs=["snapshot-001.md"],
        transcript_refs=["transcript:1"],
        preview_chars=12,
    )

    assert payload["version"] == "browser_assist_session_v1"
    assert payload["page_url_hash"].startswith("sha256:")
    assert payload["page_title_hash"].startswith("sha256:")
    assert "example.test" not in json.dumps(payload)
    assert "Private Page Title" not in json.dumps(payload)
    assert payload["text_preview"] == "alpha beta…"
    assert payload["text_hash"].startswith("sha256:")
    assert payload["openrecall_entry_refs"] == ["openrecall.entry:7"]
    assert payload["playwright_snapshot_refs"] == ["snapshot-001.md"]
    assert payload["transcript_refs"] == ["transcript:1"]
    assert payload["non_authoritative"] is True
    assert payload["artifact_hash"].startswith("sha256:")


def test_browser_assist_metadata_only_suppresses_preview_but_keeps_hash():
    payload = build_browser_assist_session(
        session_id="browser-assist-2",
        task_label="read page",
        started_at="2026-06-04T00:00:00Z",
        text_preview="visible page text",
        storage_mode="metadata_only",
    )

    assert payload["storage_mode"] == "metadata_only"
    assert payload["text_preview"] is None
    assert payload["text_hash"].startswith("sha256:")


def test_browser_assist_session_emits_no_semantic_labels():
    payload = build_browser_assist_session(
        session_id="browser-assist-3",
        task_label="accessibility capture",
        started_at="2026-06-04T00:00:00Z",
        text_preview="observed only",
    )

    forbidden = {"summary", "sentiment", "intent", "emotion", "diagnosis", "risk_score"}
    assert forbidden.isdisjoint(payload.keys())


def test_browser_assist_session_preserves_pnf_residuals_as_observer_only():
    pnf = {
        "predicate": "user_requested_find_on_page",
        "structural_signature": "browser_assist_task_candidate",
        "roles": {"object": {"value": "discussed item", "entity_type": "ui_reference"}},
        "wrapper": {"evidence_only": True},
        "provenance": ["transcript:1", "playwright.snapshot:1"],
    }

    payload = build_browser_assist_session(
        session_id="browser-assist-4",
        task_label="find discussed item",
        started_at="2026-06-04T00:00:00Z",
        pnf_candidates=[pnf],
        task_identity_residual="partial",
        lifecycle_residual="no_typed_meet",
    )

    assert payload["pnf_candidates"] == [pnf]
    assert payload["task_identity_residual"] == "partial"
    assert payload["lifecycle_residual"] == "no_typed_meet"
    assert payload["kanban_projection_policy"] == "observer_only"
    assert payload["non_authoritative"] is True
