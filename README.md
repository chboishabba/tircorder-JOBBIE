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

## Proven Abilities

Current repo-backed capabilities include:

- production capture/transcription paths
- local and remote backend support
- queue/scheduling logic
- downstream receipt and envelope handling
- documented integration points into the broader suite

What that means in practice:

- TiRCorder is already more than a one-off recorder script
- it already fits into a larger provenance-aware workflow
- it can operate in constrained environments where compute/setup details matter

## Quick Start

### Prerequisites

- Python `3.8+`
- `ffmpeg` on `PATH`
- optional GPU runtimes if you want accelerated transcription
- optional Rust toolchain in environments where certain wheels are not
  prebuilt

### Basic launch

```bash
git clone https://github.com/chboishabba/tircorder.git
cd tircorder
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
- SensibLaw makes bounded reviewed structure
- StatiBaker preserves time/state around the process

## Where To Find Things

### Start here

- roadmap:
  [docs/roadmap.md](docs/roadmap.md)
- accessibility:
  [accessibility.md](accessibility.md)
- financial timeline note:
  [docs/financial_timeline.md](docs/financial_timeline.md)
- interface/visualisation sketches:
  [docs/visualiser_interface.md](docs/visualiser_interface.md)

### Configuration and integration

- config surface:
  `tircorder/interfaces/config.py`
- suite integration notes:
  see the SensibLaw integration section in this README

## WebUI vs Backend APIs

- The Gradio/WebUI path is synchronous: you call it and wait for the finished
  result.
- The backend API path is queued: you submit work, then poll for status.
- TiRCorder supports both; choose based on the deployment and workload.

## What TiRCorder Is Not

TiRCorder is not the suite’s interpretation layer.

Its job is to capture, transcribe, and hand off material cleanly so other
layers can review or preserve it.

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
