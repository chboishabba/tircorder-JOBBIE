# Update Log

## Scanner and state handling
- Scanner now records each discovered file in the database and queues its ID for downstream work, preventing mismatched references.
- State loading reconstructs the known-files cache from folder paths and filenames so change detection remains reliable.

## WhisperX-WebUI envelope export
- Added a non-semantic adapter to emit SB execution envelopes plus segment events from WhisperX-WebUI transcripts.
- Envelope export is controlled via `transcription.webui.emit_envelope` and writes alongside the transcript (or `envelope_dir`).
- Tests cover provenance, confidence retention, and absence of semantic labels.
