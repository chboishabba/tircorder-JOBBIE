# TiRCorder Roadmap

TiRCorder is evolving from a command-line prototype into a polished suite of
recording, transcription, and analytics tools for the wider ITIR ecosystem.
This roadmap captures the most impactful initiatives currently in motion.

Roadmap language distinguishes **implemented**, **integrated/partial**, and
**design target** states.  A security, privacy, accessibility, or compliance
goal is not treated as shipped merely because it is documented.

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

## 2026: SensibLaw integration (deterministic substrate)
- **Layer 0 alignment**: normalize transcripts/notes into `Document` → `Sentence` → `Token`.
- **Utterance anchoring**: map `Utterance` ↔ `Sentence` via `UtteranceSentence`.
- **Identity unification**: resolve `speakers` into shared `Actor` + detail/alias tables.
- **Lexeme/concept population**: feed `lexemes`, `concepts`, `phrase_occurrences`.
- **Finance provenance**: add `accounts`, `transactions`, `transfers` and link with
  `FinanceProvenance` + `EventFinanceLink`.
- **Shared infrastructure**: adopt deterministic normalizers, matchers, ingestion utilities, and FTS5 indexing.

## 2026: Rights-first BIDI substrate

### Implemented
- **Authority is explicit**: sensitive actions are evaluated against receipts
  scoped to subject, purpose, action, and data class.
- **Reverse inference gates**: possession does not imply authority; observation
  does not determine legal capacity; diagnosis/disability does not imply
  permission.
- **FHIR minimisation substrate**: health-record imports can remain meta-only
  rather than silently promoting clinical free text and attachments.
- **Provenance separation**: explicit joins and receipts preserve where an
  observation came from without promoting integrity into truth.

### Integrated / partial
- **Accessibility**: retain WCAG-oriented timeline work while broadening testing
  to alternate inputs, screen readers, easy-read, and sensory-reduced modes.
- **Global health interchange**: use FHIR and thin regional adapters rather
  than a separate record ontology for each country.
- **Suite policy receipts**: connect policy outcomes to SensibLaw/StatiBaker
  provenance surfaces without giving downstream systems implicit authority.

### Design targets
- **Supported decision-making**: standing instructions, advance preferences,
  scoped supporter/representative roles, time-bounded emergency authority, and
  preservation of the subject's own account.
- **Cultural and collective governance**: purpose-bound cultural/sacred data
  controls, language support, and jurisdiction/community-specific governance
  where appropriate, without inferring race or culture from traces.
- **Policing and coercion resistance**: least-data disclosure, duress-aware
  interactions, independent review paths, and explicit separation of a police
  record from an adjudicated fact.
- **User-rights workflows**: access, correction, restriction, export,
  withdrawal, erasure/cryptographic retirement, objection, complaint, and
  human-review pathways.
- **External policy engine**: project the tested rights semantics into
  OPA/Rego or an equivalent mature deterministic policy engine as deployment
  complexity grows.
- **Regional medical connectors**: expand authorised patient-access lanes for
  Australia, Europe/UK, North America, and other regions while preserving the
  common FHIR/minimisation boundary.

## BIDI regression obligations

Future features should retain these non-collapse boundaries:

```text
recording / imported record   ->/ authority to disclose
behavioural trace             ->/ legal capacity
health/disability label       ->/ reduced rights
care/support relationship     ->/ unrestricted authority
emergency receipt             ->/ permanent authority
police involvement            ->/ guilt
signed provenance             ->/ truth
FHIR import                   ->/ clinical interpretation
cultural/location trace       ->/ inferred race/culture
```

See [RIGHTS_FIRST_BIDI.md](RIGHTS_FIRST_BIDI.md) for the architecture contract.

## Community Contributions
We welcome ideas and prototypes. Please open a GitHub Discussion or issue with
"[Roadmap]" in the title so we can collaborate on prioritization.
