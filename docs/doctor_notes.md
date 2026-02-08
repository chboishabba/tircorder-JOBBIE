# Doctor Notes Integration

TiRCorder can ingest clinician notes and visit summaries from a local export
folder and emit **story events** that reference the files.

Guardrails:
- `docs/planning/health_data_connector_guardrails_20260208.md`

## Supported Inputs
- A directory containing note artifacts:
  - `*.txt`, `*.md` (optional text ingestion, off by default)
  - `*.pdf` (metadata only; no PDF text extraction in TiRCorder)

## Timestamp Strategy
To avoid relying on filesystem `mtime`, the connector attempts to parse a
timestamp from filenames. Recommended filename prefixes:
- `YYYY-MM-DD_...`
- `YYYYMMDD_...`
- `YYYY-MM-DDTHHMMSSZ_...`

If no timestamp is found, the connector falls back to an explicit `collected_at`
argument (or last resort: `mtime`).

## Default Safety Posture
- **Meta-only by default**:
  - `sha256`, file size, filename, extension
  - optional lightweight labels (e.g., `doc_kind="doctor_note"`)
- Optional mode may include extracted text for `txt/md` only (never for `pdf`).

## Handwritten Notes and OCR
Medical notes are often handwritten or scanned.

- TiRCorder does not OCR PDFs/images by default. It records the artifact and a
  stable hash so you can re-run OCR later without losing provenance.
- Local OCR can be attempted to make artifacts searchable, but results may be
  poor on messy handwriting.
- Frontier multimodal models (e.g., ChatGPT-class) often do better on messy
  handwriting because they can use context clues, but this typically implies
  sending images off-device. That path must be explicit opt-in and treated as
  an observer transcription hypothesis (never authoritative).

## Emitted Event Shape
- `actor`: `"user"` (configurable)
- `action`: `"doctor_note"`
- `details`:
  - `sha256`
  - `file_size_bytes`
  - `filename`
  - `ext`
  - `doc_kind`
  - (optional) `text`
