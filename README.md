# TiRCorder: Part of the ITIR Suite

## Overview
TiRCorder is the voice-activated recording and transcription component of the
Intergenerational Trauma-Informed Identity Rebuilder (ITIR) toolset. The
platform focuses on secure, ethical, and accessible data capture for
communities managing intergenerational trauma. TiRCorder is currently evolving
from its original command-line utility toward a full GUI experience while
retaining its CLI and API for advanced operators. Licensed under the Mozilla
Public License (MPL 2.0), the suite prioritizes transparency, privacy, and
operational resilience.
<img width="9011" height="20036" alt="NotebookLM Mind Map(7)" src="https://github.com/user-attachments/assets/304af15e-1533-4b99-8054-fd85078ea382" />

## Quick Start

### Prerequisites
- Python **3.8+** (tested with 3.9.18 on Arch Linux). Please note that only some kernel versions and cards are officially supported by ROCm, though compatibility has been broadened by [TheRock](https://github.com/ROCm/TheRock).
- [`ffmpeg`](https://ffmpeg.org/) available on your PATH.
- Optional: GPU runtimes (CUDA, ROCm, or Metal) if you plan to leverage
  accelerated Whisper/cTranslate2 inference. Install platform-specific drivers
  before running TiRCorder.
- Optional: Rust toolchain for environments where `tiktoken` wheels are not
  prebuilt (`cargo`, `rustc`, and `setuptools-rust`).

### Install and Launch
```bash
git clone https://github.com/chboishabba/tircorder.git
cd tircorder
python tircorder.py  # or use tircorder-linux.py on Linux
```

### Environment Checks
```bash
python --version
python - <<'PY'
import torch
print(f"CUDA available: {torch.cuda.is_available()}")
PY
```

## Architecture Highlights
- **Entry points**: `tircorder.py` and `tircorder-linux.py` bootstrap dependency
  checks and launch the client/server runtime.
- **Orchestration**: `main.py` wires queues, models, and worker threads for
  scanning, transcription, and post-processing.
- **Workers**:
  - `scanner` monitors configured directories and enqueues new audio assets.
  - `transcriber` orchestrates Whisper or cTranslate2 jobs.
  - `wav2flac` converts intermediary audio artifacts for storage efficiency.
- **Interfaces and tooling**: modules in `tircorder/interfaces/` expose config
  management, scheduling, and client coordination utilities.

## Feature Highlights
- **Voice activation** with configurable sensitivity for all-day capture.
- **Activity-based recording management** to optimize resource usage.
- **Task scheduling** and queueing to prevent processing conflicts.
- **GPU acceleration** (with CPU fallback) for high-throughput transcription.
- **Remote transcription support** so heavy workloads can be offloaded to a
  dedicated server.
- **Calendar and timeline visualizations** for historical insight.
- **Update tracking** via [`Updates.md`](Updates.md) for release notes.

## SensibLaw integration (Layer 0–1 alignment)
TiRCorder is the event/narrative capture layer in the shared SensibLaw ontology.
To keep provenance and identity stable, TiRCorder aligns to the shared substrate:

- Normalize transcripts/notes into `Document` → `Sentence` → `Token` (Layer 0).
- Anchor `Utterance` to `Sentence` via `UtteranceSentence`.
- Resolve `speakers` into shared `Actor` records; keep actor traits in detail/alias tables.
- Populate `lexemes`, `concepts`, and `phrase_occurrences` for canonical term mapping.
- Link finance timelines through `accounts`, `transactions`, `transfers`, plus
  `FinanceProvenance` and `EventFinanceLink`.
- Use deterministic SensibLaw utilities (normalizers, matchers, resilient ingestion).

### Feature Matrix
| Capability | Status | Notes |
| --- | --- | --- |
| Voice-activated recording | Production | Tunable thresholds via configuration.
| Whisper & cTranslate2 transcription | Production | Switch engines per deployment.
| Remote WebUI transcription | Production | Authenticate with username/password or API key.
| Adaptive recording intervals | In development | Storage-saving heuristics under active testing.
| Speaker diarization | Production | Planned integration with WhisperX.
| Word-level transcripts & confidence | Production | Dependent on diarization pipeline.
| Sentiment, timeline, and calendar dashboards | Prototype | Hooks for external activity sources (YouTube, Google Docs, Zapier).
| Web-based operator interface | Prototype | Gradio interface available; dedicated UX in progress.

## Configuration
TiRCorder reads runtime settings through
`tircorder/interfaces/config.py`, which persists JSON configuration files.
Follow these steps to tailor an installation:

1. **Locate the configuration file**:
   - Defaults to `~/.tircorder/config.json`.
   - Override the location with the `TIRCORDER_CONFIG_PATH` environment
     variable.
2. **Inspect existing values** using the helper:
   ```python
   from tircorder.interfaces.config import TircorderConfig
   print(TircorderConfig.get_config())
   ```
3. **Choose a transcription backend** by setting `transcription.method` to
   `"whisper"`, `"ctranslate2"`, or `"webui"`.
4. **Authenticate remote services** by filling the `transcription.webui`
   section:
   ```json
   {
     "transcription": {
       "method": "webui",
       "webui": {
         "base_url": "https://webui.example",
         "username": "operator",
         "password": "s3cret",
         "timeout": 900,
         "options": {
           "temperature": 0.1
         }
       }
     }
   }
   ```
   5. **Persist updates** with `TircorderConfig.set_config({...})`; the helper will
      create the directory tree if it does not yet exist.

### WebUI vs. backend APIs
- The WhisperX Gradio WebUI endpoint (`/_transcribe_file`) is a synchronous
  call: the request remains open until the transcription is finished and the
  response contains the final outputs. There is no status or polling route
  available for these endpoints beyond the UI's own progress bar.
- For queued jobs with progress reporting, target the backend FastAPI service
  instead: `POST /transcription` enqueues work and returns an identifier,
  `GET /task/{identifier}` reports status/results, and background-music
  separation downloads are available via `GET /task/file/{identifier}`.

## Roadmap & Vision
Explore the long-term strategy, release themes, and community priorities in the
[roadmap](docs/roadmap.md). For a historical perspective of TFYQA, see the
[archived site](https://web.archive.org/web/20070831084954/http://www.tfyqa.biz/).

## Contribution Guidelines
We warmly welcome contributions.
1. Fork the repository and create a feature branch.
2. Install development dependencies:
   ```bash
   pip install -r requirements-dev.txt
   ```
3. Run the test suite before submitting a pull request:
   ```bash
   PYENV_VERSION=3.10.17 PYTHONPATH=. pytest tests/test_calendar_utils.py -q
   ```
4. Provide a clear summary and include command output when opening a PR.
5. For larger ideas, open an issue or discussion first to coordinate with the
   maintainers.

## Documentation & Further Reading
- [3D Timeline Axis Priorities](docs/3d_timeline.md)
- [Accessibility commitments](accessibility.md)
- [Financial timeline concepts - please note these functions are being moved to SensibLaw but will still remain available for personal use within ITIR](docs/financial_timeline.md)
- [Interface and visualisation sketches](docs/visualiser_interface.md)

## Accessibility
The generated web interface uses semantic HTML and provides transcripts for
audio clips, but it currently lacks ARIA roles, skip-navigation links, and other
enhancements that improve screen-reader and keyboard support. We document
implemented accessibility tools and the TODO roadmap in
[accessibility.md](accessibility.md) and welcome community feedback as we work
toward WCAG 2.1 AA compliance.

## License
ITIR and TiRCorder are products of TFYQA.biz provided under the
[Mozilla Public License 2.0](https://www.mozilla.org/en-US/MPL/).
All rights are reserved where permitted.

## Acknowledgements & Support
Massive thank you to
[lamikr](https://github.com/lamikr/rocm_sdk_builder),
[xuhuisheng](https://github.com/xuhuisheng/rocm-gfx803), and
[robertrosenbusch](https://github.com/robertrosenbusch/gfx803_rocm) for enabling
continued development. If TiRCorder has helped you or your community, consider
[sponsoring a coffee](https://www.paypal.com/paypalme/JohnABrown).
