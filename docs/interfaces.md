# TiRCorder Interface Contract (Intended)

## Intersections
- Upstream audio/event capture for ITIR operations.
- Uses `WhisperX-WebUI/` or local transcription paths for text generation.
- Emits timeline/evidence records consumed by `SensibLaw/` and `StatiBaker/`.

## Interaction Model
1. Capture or ingest audio/event streams.
2. Queue and execute transcription/processing workflows.
3. Normalize outputs into timeline-ready, provenance-carrying records.
4. Export artifacts for legal and state-compilation layers.

## Exchange Channels
### Channel A: Capture Ingress
- Input: microphone/audio files and scheduling directives.
- Output: queued jobs with capture metadata.

### Channel B: Processing Control
- Input: runtime config for model choice, queue policy, and batching.
- Output: job lifecycle events and failure states.

### Channel C: Transcript Egress
- Output: transcripts, timestamps, diarization metadata, and references.
- Consumer: `SensibLaw/` ingest and timeline tools.

### Channel D: Timeline/Event Egress
- Output: event-linked records with provenance handles.
- Consumer: `StatiBaker/` and ITIR orchestration.
