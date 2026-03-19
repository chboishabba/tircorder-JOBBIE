# Update Log

## Web surface transition
- Clarified repo direction: `itir-svelte/` is the sole intended web interface
  for ITIR-suite going forward.
- `Pelican/` and `Zola/` remain in `tircorder-JOBBIE/` only as
  legacy/reference material during migration.
- New product-facing web behavior should be implemented in `itir-svelte/`,
  with legacy helpers retained only long enough to port or verify behavior
  before deletion.

## Scanner and state handling
- Scanner now records each discovered file in the database and queues its ID for downstream work, preventing mismatched references.
- State loading reconstructs the known-files cache from folder paths and filenames so change detection remains reliable.

## WhisperX-WebUI envelope export
- Added a non-semantic adapter to emit SB execution envelopes plus segment events from WhisperX-WebUI transcripts.
- Envelope export is controlled via `transcription.webui.emit_envelope` and writes alongside the transcript (or `envelope_dir`).
- Tests cover provenance, confidence retention, and absence of semantic labels.

## Health export connectors (meta-only by default)
- Added local-import connectors for health data exports under `integrations/medical/`:
  - FHIR export ingestion (Bundle/NDJSON) -> story events
  - scans folder ingestion (DICOM/exported images/PDFs) -> story events
  - doctor notes folder ingestion (txt/md/pdf refs; optional text for txt/md) -> story events
- Default posture is meta-only: hashes + file metadata; no base64 attachments or PDF text extraction.
