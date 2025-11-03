# ITIR Suite Roadmap

## TiRCorder

TiRCorder is evolving from a command-line prototype into a polished suite of
recording, transcription, and analytics tools for the wider ITIR ecosystem.
This roadmap captures the most impactful initiatives currently in motion.

## 2024: Product Foundations
- **Stabilize cross-platform packaging** for Linux, Windows, and macOS
  distributions, including dependency bootstrapping and GPU detection.
- **Refine operator UX** with guided onboarding flows, updated CLI messaging,
  and the first iteration of a GUI tailored to low-technical-literacy users.
- **Expand transcription backends** by hardening the WebUI integration and
  exposing additional Whisper/CT2 tuning parameters in configuration files.
- **Data governance reviews** to document encryption-at-rest, retention
  policies, and automated archival mechanisms across deployments.

## 2025: Insight-Driven Workflows
- **Speaker diarization and word-level transcripts** for precise attribution
  and follow-up actions.
- **Sentiment, timeline, and calendar dashboards** that merge transcript
  analytics with external context such as calendars, messaging, or CRM data.
- **Automated compliance auditing** linking recordings with policy checks and
  exception workflows.
- **Operator co-pilots** that surface suggested summaries and follow-up tasks
  in real time.

## Community Contributions
We welcome ideas and prototypes. Please open a GitHub Discussion or issue with
"[Roadmap]" in the title so we can collaborate on prioritization.


## Near-Term Goals (0-3 months)

| Goal | Description | Status | Links |
| --- | --- | --- | --- |
| Chat History Integration | Consolidate conversation archives into TiRCorder to enrich context for investigators. | In Progress | [Chat archival plan](docs/twitter_backup.md) |
| GUI Transition Planning | Finalize interaction design updates for moving from CLI-first flows to the new GUI shell. | Planned | [Interface concepts](docs/visualiser_interface.md) |
| Data Integrity Audits | Automate checks for dangling transcripts, audio, and calendar entries to prevent analysis gaps. | Planned | [Integrity checklist](check_db_integrity.py) |

## Mid-Term Goals (3-9 months)

| Goal | Description | Status | Links |
| --- | --- | --- | --- |
| Unified Timeline Visualizer | Merge the 3D, ribbon, and financial timelines into a cohesive investigative dashboard. | Planned | [3D timeline](docs/3d_timeline.md), [Ribbon goals](docs/ribbon_timeline_goals.md), [Financial timeline](docs/financial_timeline.md) |
| Cross-Source Sentiment Layer | Extend sentiment analysis to correlate across transcripts, emails, and social feeds. | Planned | [Sentiment tooling](sentiment_analysis.py) |
| Investigator Collaboration Suite | Introduce shared annotations, task assignments, and audit logs across teams. | Planned | [TiRCorder outline](Outline.md) |

## Long-Term Goals (9-18 months)

| Goal | Description | Status | Links |
| --- | --- | --- | --- |
| AI-Assisted Briefings | Generate automated summaries and recommended next steps for case briefings using contextual memory. | Planned | [TiRCorder vision](README.md) |
| Full GUI Transition | Complete migration from legacy CLI utilities to the cross-platform desktop client with modular plugins. | Planned | [Bevy app prototype](bevy_app/) |
| Live Data Fusion | Support streaming integrations (e.g., social media firehose, financial feeds) with real-time alerting and triage. | Planned | [Integration scripts](integrations/) |
