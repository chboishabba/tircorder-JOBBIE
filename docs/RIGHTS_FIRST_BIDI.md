# Rights-First BIDI Architecture

TiRCorder captures unusually sensitive material. The architecture therefore
separates what the system **observes** from what a person or operator is
**authorised or permitted to do** with those observations.

This document describes product invariants and development targets. It is not
a claim that every listed legal regime or control is already implemented, and
it is not legal advice.

## Core BIDI boundary

Forward direction:

```text
captured material
  -> typed data class
  -> requested action
  -> stated purpose
  -> authority receipt
  -> permission / obligation receipts where governed
  -> policy decision
  -> provenance/audit receipt
```

Reverse direction is intentionally non-factorable:

```text
possession of data          != authority to process/share it
recorded behaviour          != legal capacity determination
diagnosis/disability label  != permission or diminished rights
police involvement          != guilt or factual correctness
care/support role           != unrestricted representative authority
emergency                   != permanent authority
FHIR/medical record         != clinical interpretation
cultural metadata           != licence for secondary use
same content                != same provenance
scientific result           != prior consent or benefit sharing
```

`tircorder.rights_policy` owns the first executable form of these boundaries.

## Governed cultural knowledge

The cultural/sacred lane is derived from the repository's Agda knowledge-
governance constructions rather than a flat `CulturalFlags` Boolean. Content,
provenance, authority, permission, and obligation remain separate coordinates.

For culturally governed processing, ordinary authority is necessary but not
sufficient. The current Python gate additionally requires:

```text
authority for subject + purpose + action + data class
+ separately scoped permission
+ matching provenance when declared
+ acknowledgement of required obligations
```

This lets TiRCorder represent cases where someone may lawfully possess or
administer material without being permitted to disclose every layer of it.

Transformation receipts use four effects:

```text
preserved | added | erased | unresolved
```

A detached-content projection is calibrated as preserving content while
marking provenance, authority, permission, and obligation as erased. Downstream
code must not reconstruct erased governance coordinates from the surviving
content surface.

This is intentionally compatible with later collective-governance, Indigenous
data-sovereignty, community protocol, attribution, and benefit-sharing modules
without claiming that one generic policy implements any particular community's
law or protocol.

## Rights surface

The product roadmap should make the following actions exercisable without
requiring users to understand a particular jurisdiction's terminology:

- access personal data
- correct inaccurate information
- delete or cryptographically retire data
- pause or restrict processing
- export and transfer data
- object to particular purposes
- opt out of sale or onward sharing
- limit sensitive-data use
- obtain meaningful information about automated processing
- request human review where applicable
- use anonymity or pseudonymity where lawful and practicable
- know why data is collected and used
- see who accessed or received data
- withdraw consent for future processing
- challenge handling and make a complaint
- receive equal service when exercising privacy rights

Jurisdiction modules can map these common actions to GDPR/UK GDPR, Australian
Privacy Principles, US state regimes, Canadian privacy law, and other local
requirements without changing the core user model.

## Disability and supported decision-making

Accessibility is not the same thing as authority. TiRCorder should support
multiple communication and interaction modes while preserving the subject as a
participant in decisions wherever possible.

Design targets include:

- plain-language and easy-read views
- keyboard, switch, screen-reader and alternative-input operation
- sensory-reduced modes
- communication/AAC-friendly capture and review
- standing instructions and advance preferences
- supporter/representative roles with explicit scopes
- time-bounded emergency receipts and later review
- preservation of the subject's own account alongside supporter accounts

A fluctuating presentation must not be silently promoted into a global or
permanent capacity conclusion.

## Race, culture and collective rights

Cultural context can alter appropriate governance without becoming an inferred
attribute or stereotype. Product targets include purpose-bound cultural data
controls, language support, community/collective governance where applicable,
and compatibility with Indigenous data-sovereignty approaches such as CARE and
locally applicable frameworks.

The system must not infer race, ethnicity, culture, sacred status, community
authority, or policing risk merely from behavioural or location traces.

## Policing, safety and coercion resistance

Evidence-preservation features must not become surveillance features. The
roadmap therefore separates:

- capture from disclosure
- integrity from truth
- chain-of-custody from guilt
- emergency assistance from continuing authority
- a police record from an adjudicated fact

High-impact disclosure paths should eventually support explicit authority,
least-data disclosure, provenance receipts, time limits, independent review,
and safe/duress-aware interaction patterns.

## Global health integration

The existing FHIR connector is the standards-first substrate for health data.
Regional connectors should prefer authorised APIs and user-controlled exports:

```text
regional/national record source
  -> FHIR or thin regional adapter
  -> minimized TiRCorder event
  -> rights/purpose gate
  -> local timeline / explicit downstream promotion
```

Candidate regional lanes include Australian My Health Record/ePrescription
workflows, European patient-access infrastructure, NHS pathways, US patient
FHIR/Blue Button-style access, and other national systems as interfaces permit.

Import does not imply interpretation, and integration availability does not
imply regulatory approval.

## Standards and reusable infrastructure

Prefer mature components and thin adapters:

- HL7 FHIR for health interchange
- SQLite FTS5 before a custom search engine
- OPA/Rego or an equivalent deterministic policy layer as policy complexity grows
- signed evidence/receipt packs using established signature tooling
- established ASR engines rather than custom speech recognition
- standard graph/layout engines rather than custom layout mathematics

The in-process `rights_policy` module is intentionally small. It establishes
semantics and tests that can later be projected into OPA/Rego without changing
the rights model.

## Completion model

Use three states in user-facing documentation:

- **Implemented** — exercised by repository code and tests.
- **Integrated/partial** — substrate exists, but the end-to-end right/control is incomplete.
- **Design target** — documented goal; must not be marketed as an existing control.

Security, privacy and compliance claims should always be traceable to one of
those states.
