# TiRCorder

TiRCorder is the suite's capture and transcription intake layer.

It is the part of the workspace that focuses on getting spoken material and
related capture artifacts into a form the rest of the suite can use.

In plain language:

- it records or ingests audio
- it runs transcription
- it keeps the outputs available for downstream review
- it can pass those outputs into other suite components instead of leaving them
  stranded as loose files

## What TiRCorder Does

TiRCorder currently provides:

- voice-activated or workflow-driven recording
- transcription using Whisper, cTranslate2, or remote WebUI/backends
- queueing/scheduling around transcription work
- local and remote transcription pathways
- downstream fan-out into other suite surfaces such as SensibLaw and
  StatiBaker
- standards-oriented medical import, including a privacy-minimising FHIR path
- an initial rights-first policy boundary for sensitive processing

## What You Can Do With It Today

### 1. Capture audio and turn it into transcript artifacts

The basic job is simple:

- collect audio
- transcribe it
- persist usable artifacts for later review

Typical outputs include:

- transcript JSON
- execution-envelope style artifacts
- downstream receipt files

### 2. Use local or remote transcription backends

TiRCorder can work with:

- local Whisper/cTranslate2 style backends
- remote backend/API paths
- WebUI-linked paths when that better matches the deployment

That matters because the project is designed for real environments with uneven
hardware, not only an ideal local GPU setup.

### 3. Feed the rest of the suite

TiRCorder is not meant to be the end of the process.

It can hand outputs onward so that:

- `SensibLaw` can ingest transcript-related artifacts into structured review
  surfaces
- `StatiBaker` can preserve execution/activity traces as read-only state

### 4. Keep observation separate from authority

Sensitive data needs more than a successful import.  The rights-first policy
kernel separates the observed material from the authority to process or share
it.  An authority receipt is scoped by subject, purpose, action, and data
class.

The reverse inferences are intentionally blocked:

- possession of data does not prove authority
- observed behaviour does not determine legal capacity
- diagnosis or disability does not grant access permission
- integrity/provenance does not prove an allegation true
- emergency authority does not automatically become continuing authority

See [Rights-First BIDI Architecture](docs/RIGHTS_FIRST_BIDI.md) for the wider
product model.

## Proven Abilities

Current repo-backed capabilities include:

- production capture/transcription paths
- local and remote backend support
- queue/scheduling logic
- downstream receipt and envelope handling
- documented integration points into the broader suite
- FHIR import with a meta-only, PHI-minimising default
- purpose/action/data-class scoped policy decisions for sensitive processing

What that means in practice:

- TiRCorder is already more than a one-off recorder script
- it already fits into a larger provenance-aware workflow
- it can operate in constrained environments where compute/setup details matter
- sensitive-data possession is not treated as permission to use that data

## Security, Rights, and Completion State

TiRCorder is being developed for high-sensitivity personal information.  We do
not treat a design goal as a shipped control.

| Area | State | Current boundary |
| --- | --- | --- |
| Capture and transcription | **Implemented** | Local/remote paths and queueing exist |
| Provenance/downstream receipts | **Implemented / partial** | Existing receipt and explicit-link substrates |
| FHIR medical import | **Implemented** | Meta-only default; raw PHI/attachments suppressed |
| Rights/purpose authority kernel | **Implemented** | Subject + purpose + action + data-class scope |
| WCAG-oriented accessibility | **Implemented / partial** | Existing accessible timeline; broader testing remains |
| Supported decision-making / disability safeguards | **Design target** | BIDI invariants documented; broader UX not yet shipped |
| Cultural / collective governance safeguards | **Design target** | Must not infer identity or secondary-use permission |
| Policing / coercion-resistant disclosure controls | **Design target** | Capture, integrity, truth, and authority remain distinct |
| Full consent / access / erasure dashboard | **Design target** | Rights model exists; end-to-end UI remains to build |
| External OPA/Rego policy engine | **Design target** | Small in-process kernel establishes semantics first |
| Global regional health connectors | **Integrated / partial** | FHIR substrate exists; regional coverage remains uneven |

### Rights the product is being designed to support

- Access personal data
- Correct inaccurate information
- Delete or cryptographically retire data
- Pause or restrict processing
- Export and transfer data
- Object to particular processing purposes
- Opt out of sale or onward sharing
- Limit sensitive-data use
- Understand significant automated processing
- Request human review where applicable
- Use anonymity or pseudonymity where practicable
- Know why data is collected and used
- See who accessed or received data
- Withdraw consent for future processing
- Challenge handling and make complaints
- Receive equal service when exercising privacy rights

These are global product goals, not a claim that every workflow or jurisdiction
is already implemented.  See [Rights-First BIDI Architecture](docs/RIGHTS_FIRST_BIDI.md)
for scope and completion semantics.

## Quick Start

### Prerequisites

- Python `3.10+`
- `ffmpeg` on `PATH`
- optional GPU runtimes if you want accelerated transcription
- optional Rust toolchain in environments where certain wheels are not
  prebuilt

### Basic launch

```bash
git clone https://github.com/chboishabba/tircorder-JOBBIE.git
cd tircorder-JOBBIE
python tircorder.py
```

Linux-specific alternative:

```bash
python tircorder-linux.py
```

### Environment checks

```bash
python --version
python - <<'PY'
import torch
print(f"CUDA available: {torch.cuda.is_available()}")
PY
```

## Common Workflows

### Local transcription workflow

Use this when the same machine is doing capture and transcription.

Relevant surfaces:

- `tircorder.py`
- `tircorder-linux.py`
- `main.py`

### Remote or WebUI-backed transcription workflow

Use this when capture and heavy transcription should be separated.

Relevant configuration/docs:

- `tircorder/interfaces/config.py`
- the `transcription.webui` configuration section
- the WebUI vs backend API notes in this README

### Medical/FHIR import workflow

Use the medical integration layer for user-controlled health-record exports.
The existing FHIR path defaults to minimal metadata rather than silently
promoting clinical free text into the general timeline.

Relevant surfaces:

- `integrations/medical/fhir_export.py`
- `integrations/medical/my_health_record.py`
- [FHIR export integration](docs/fhir_export.md)

### Downstream suite integration

Use this when transcript outputs should feed the rest of the suite rather than
stopping at raw transcript files.

Current downstream expectations include:

- transcript JSON artifacts
- execution envelope artifacts
- downstream receipts
- optional SensibLaw sink
- optional StatiBaker sink

## Feature Highlights

- voice-activated recording
- queue-aware transcription flow
- GPU acceleration with CPU fallback
- remote transcription support
- timeline/calendar-oriented history surfaces
- integration hooks for the broader suite
- standards-first health-data import
- explicit rights/authority policy boundary

## Configuration

Runtime settings are handled through:

- `tircorder/interfaces/config.py`

Key ideas:

- config defaults to `~/.tircorder/config.json`
- `TIRCORDER_CONFIG_PATH` can override the location
- `transcription.method` chooses the backend
- `transcription.webui` config controls remote/WebUI-backed paths

If you are using downstream fan-out, make sure the SensibLaw and StatiBaker
target paths are configured intentionally rather than left ambiguous.

## Relationship To The Rest Of The Suite

TiRCorder is the capture/intake layer.

It sits beside:

- `WhisperX-WebUI`, which can serve as a transcription service/UI surface
- `SensibLaw`, which turns downstream artifacts into structured review surfaces
- `StatiBaker`, which preserves execution/state traces

Short version:

- TiRCorder gets material in
- TiRCorder preserves rights/authority boundaries around sensitive actions
- SensibLaw makes bounded reviewed structure
- StatiBaker preserves time/state around the process

## Where To Find Things

### Start here

- roadmap:
  [docs/roadmap.md](docs/roadmap.md)
- rights-first architecture:
  [docs/RIGHTS_FIRST_BIDI.md](docs/RIGHTS_FIRST_BIDI.md)
- accessibility:
  [accessibility.md](accessibility.md)
- provenance:
  [docs/PROVENANCE.md](docs/PROVENANCE.md)
- FHIR integration:
  [docs/fhir_export.md](docs/fhir_export.md)
- financial timeline note:
  [docs/financial_timeline.md](docs/financial_timeline.md)
- interface/visualisation sketches:
  [docs/visualiser_interface.md](docs/visualiser_interface.md)

### Configuration and integration

- config surface:
  `tircorder/interfaces/config.py`
- downstream adapter:
  `tircorder/downstream.py`
- policy semantics:
  `tircorder/rights_policy.py`

## WebUI vs Backend APIs

- The Gradio/WebUI path is synchronous: you call it and wait for the finished
  result.
- The backend API path is queued: you submit work, then poll for status.
- TiRCorder supports both; choose based on the deployment and workload.

## What TiRCorder Is Not

TiRCorder is not the suite’s interpretation layer.

Its job is to capture, transcribe, and hand off material cleanly so other
layers can review or preserve it.  A captured observation, record, diagnosis,
police entry, or provenance receipt is not automatically a conclusion about
truth, capacity, guilt, identity, or authority.

## License

ITIR and TiRCorder are products of TFYQA.biz provided under the
[Mozilla Public License 2.0](https://www.mozilla.org/en-US/MPL/).
All rights are reserved where permitted.

## Acknowledgements

Massive thank you to
[lamikr](https://github.com/lamikr/rocm_sdk_builder),
[xuhuisheng](https://github.com/xuhuisheng/rocm-gfx803), and
[robertrosenbusch](https://github.com/robertrosenbusch/gfx803_rocm) for making
continued development on older ROCm/gfx803 environments more viable.


[![Ask DeepWiki](https://deepwiki.com/badge.svg)](https://deepwiki.com/chboishabba/tircorder-JOBBIE)
