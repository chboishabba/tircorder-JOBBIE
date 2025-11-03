# TiRCorder/ITIR Roadmap

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
