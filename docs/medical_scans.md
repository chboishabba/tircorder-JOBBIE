# Medical Scans Integration

TiRCorder can ingest scan exports from a local folder and emit **story events**
that reference scan files by hash.

Guardrails:
- `docs/planning/health_data_connector_guardrails_20260208.md`

## Supported Inputs
- A directory containing scan artifacts (metadata-only ingestion):
  - `*.dcm` (DICOM files)
  - common exported formats: `*.pdf`, `*.png`, `*.jpg`, `*.jpeg`

## What We Store (By Default)
- `sha256` of file bytes
- file size and filename
- optional coarse `scan_kind` derived from extension

TiRCorder does not parse DICOM tags by default (no `pydicom` dependency).
If richer metadata is required (modality, StudyInstanceUID, etc.), add a
downstream DICOM-aware adapter under explicit guardrails.

## OCR Note
Some scan exports (PDF/image) are effectively "scanned documents" (forms,
handwritten notes, printed discharge summaries). If you OCR them:
- local OCR is acceptable for baseline searchability but may be weak on messy
  handwriting
- frontier multimodal OCR can be higher quality but must be explicit opt-in and
  treated as non-authoritative transcription output

## Timestamp Strategy
Same as notes: prefer timestamps embedded in filenames; otherwise use explicit
`collected_at` provided by the caller.

## Emitted Event Shape
- `actor`: `"user"` (configurable)
- `action`: `"medical_scan"`
- `details`:
  - `sha256`
  - `file_size_bytes`
  - `filename`
  - `ext`
  - `scan_kind`
