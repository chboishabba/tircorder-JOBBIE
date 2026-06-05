from __future__ import annotations

import json

import pytest

from tircorder.sb_adapter import build_execution_envelope
from tircorder.simulstreaming_adapter import (
    load_simulstreaming_jsonl,
    normalize_simulstreaming_events,
    normalize_simulstreaming_jsonl,
    parse_simulstreaming_jsonl,
)


def test_normalize_simulstreaming_jsonl_maps_confirmed_text_to_segments() -> None:
    payload = normalize_simulstreaming_jsonl(
        "\n".join(
            [
                json.dumps(
                    {
                        "emission_time": 8.8,
                        "end": 0.66,
                        "status": "INCOMPLETE",
                        "text": "",
                        "unconfirmed_text": "So...",
                        "is_final": False,
                    }
                ),
                json.dumps(
                    {
                        "emission_time": 11.4,
                        "end": 8.02,
                        "status": "INCOMPLETE",
                        "text": " So,",
                        "unconfirmed_text": "please ask colleagues",
                        "is_final": False,
                    }
                ),
                json.dumps(
                    {
                        "emission_time": 12.5,
                        "end": 8.02,
                        "status": "COMPLETE",
                        "text": " So,",
                        "unconfirmed_text": "please ask colleagues",
                        "is_final": False,
                    }
                ),
                json.dumps(
                    {
                        "emission_time": 15.0,
                        "end": 12.0,
                        "status": "COMPLETE",
                        "text": " So, please ask colleagues",
                        "unconfirmed_text": "",
                        "is_final": True,
                    }
                ),
            ]
        ),
        model="simul-whisper",
        language="en",
    )

    assert payload["text"] == "So, please ask colleagues"
    assert payload["model"] == "simul-whisper"
    assert payload["language"] == "en"
    assert payload["source"] == "simulstreaming_jsonl"
    assert payload["partial_updates"][0]["unconfirmed_text"] == "So..."
    assert payload["segments"] == [
        {
            "text": "So,",
            "start": 0.0,
            "end": 8.02,
            "source": "simulstreaming_jsonl",
            "status": "INCOMPLETE",
            "emission_time": 11.4,
            "is_final": False,
        },
        {
            "text": "please ask colleagues",
            "start": 8.02,
            "end": 12.0,
            "source": "simulstreaming_jsonl",
            "status": "COMPLETE",
            "emission_time": 15.0,
            "is_final": True,
        },
    ]


def test_normalize_simulstreaming_payload_is_sb_envelope_compatible(tmp_path) -> None:
    audio_file = tmp_path / "call.wav"
    audio_file.write_bytes(b"RIFF")
    payload = normalize_simulstreaming_events(
        [
            {
                "emission_time": 1.0,
                "end": 2.0,
                "status": "COMPLETE",
                "text": "Confirmed sentence.",
                "unconfirmed_text": "",
                "is_final": True,
            }
        ],
        model="simul-whisper",
        language="en",
    )

    envelope_payload = build_execution_envelope(
        payload,
        source="simulstreaming_jsonl",
        audio_path=audio_file,
    )

    envelope = envelope_payload["execution_envelope"]
    assert envelope["source"] == "simulstreaming_jsonl"
    assert envelope["toolchain"]["model"] == "simul-whisper"
    assert envelope["toolchain"]["language"] == "en"
    assert envelope["segment_count"] == 1
    assert envelope_payload["segment_events"][0]["data"]["text"] == "Confirmed sentence."


def test_parse_simulstreaming_jsonl_rejects_invalid_lines() -> None:
    with pytest.raises(ValueError, match="line 2"):
        parse_simulstreaming_jsonl('{"text": "ok"}\nnot-json')

    with pytest.raises(ValueError, match="must be an object"):
        parse_simulstreaming_jsonl('["not", "object"]')


def test_load_simulstreaming_jsonl_file(tmp_path) -> None:
    source = tmp_path / "output.jsonl"
    source.write_text('{"text": "hello", "end": 1.0}\n\n', encoding="utf-8")

    events = load_simulstreaming_jsonl(source)

    assert events == [{"text": "hello", "end": 1.0}]


def test_unconfirmed_final_can_be_included_for_advisory_capture() -> None:
    payload = normalize_simulstreaming_events(
        [
            {
                "emission_time": 1.0,
                "end": 2.0,
                "status": "INCOMPLETE",
                "text": "",
                "unconfirmed_text": "still tentative",
                "is_final": False,
            }
        ],
        include_unconfirmed_final=True,
    )

    assert payload["text"] == "still tentative"
    assert payload["segments"][0]["status"] == "UNCONFIRMED_FINAL"
