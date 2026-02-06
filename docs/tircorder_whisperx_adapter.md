# TiRCorder WhisperX-WebUI -> SB execution envelope adapter

## Purpose
Emit SB execution envelopes plus segment events from WhisperX-WebUI
transcription output. This adapter is non-semantic: it preserves observed
values and does not add interpretive labels.

## Input
WhisperX-WebUI transcription response (JSON), including:
- `text` (full transcript)
- `segments[]` (start/end/text/speaker/confidence)
- optional `model`, `language`

## Output
A single JSON file containing:
- `execution_envelope`
- `segment_events[]`

Envelope fields (subset):
- `type`: `execution_envelope`
- `format`: `sb_execution_envelope_v1`
- `source`: `whisperx_webui`
- `toolchain.model`, `toolchain.language`
- `audio_hash` (sha256 of input audio, if provided)
- `segment_count`
- `provenance.transcript_hash`
- `provenance.adapter`: `tircorder_whisperx_webui_v1`
- `created_at` (UTC ISO8601)

Segment event fields (each `type: audio_segment`):
- `text`, `start`, `end`, `speaker`, `confidence`
- `provenance.source`, `provenance.envelope_id`
- `audio_hash` (if provided)

## Non-goals
- No summarization, sentiment, intent, emotion, or diagnosis labels.
- No re-timestamping, re-segmentation, or diarization edits.

## Configuration
Set these under `transcription.webui` in the TiRCorder config:
- `emit_envelope` (bool): enable envelope export
- `envelope_dir` (string|null): optional output directory
- `envelope_format` (string): defaults to `sb_execution_envelope_v1`

When enabled, TiRCorder writes:
- `<audio_stem>.execution_envelope.json`

If `envelope_dir` is unset, the file is written alongside the `.txt` transcript.

## Provenance rules
- Envelope IDs are derived from transcript + audio hashes.
- Transcript JSON is hashed with sorted keys; audio hash is sha256 of bytes.
- All emitted segment events carry `provenance` pointing back to the envelope.

## Test guarantees
- Provenance is present.
- Segment confidence is retained.
- No semantic labels are emitted.

