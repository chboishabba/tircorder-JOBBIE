# FHIR Export Integration

TiRCorder can ingest EHR exports in **FHIR JSON** and emit **story events**
(`event_id`, `timestamp`, `actor`, `action`, `details`) suitable for downstream
timeline tooling.

## Supported Inputs
- A single FHIR `Bundle` JSON file (`resourceType: "Bundle"`, with `entry[].resource`)
- NDJSON (newline-delimited) where each line is a FHIR resource object
- A directory containing `*.json` resources and/or `*.ndjson`

## Default Safety Posture
- **Meta-only by default**: the connector extracts minimal non-semantic fields
  and avoids emitting PHI (names, addresses, free-text narrative, base64 attachments).
- Attachments (e.g. `DocumentReference.content.attachment.data`) are not emitted.

## Normalization
Each FHIR resource becomes a story event with:
- `actor`: `"ehr"` (configurable)
- `action`: `"fhir_resource"`
- `details` (example fields):
  - `resource_type`
  - `resource_id_hash` (hashed identifier; avoids leaking raw IDs)
  - `last_updated` (when present)
  - `codes` (selected code systems/codes where present; minimized)
  - `attachment_refs` (metadata only: filename/content-type/url when present)

## Practical Notes
- For scans, EHRs often represent imaging as `ImagingStudy` plus linked
  `DiagnosticReport`. Pixel data is out of scope; ingest metadata only.
- If you want searchable note text, keep TiRCorder as the observer boundary
  and promote content into SensibLaw’s document store with explicit receipts.

