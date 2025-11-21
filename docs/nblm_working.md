The integration of TiRCorder (TR) with the SensiBlaw (SL) ontology requires structural changes focused on normalizing TiRCorder's narrative data onto the shared **Layer 0: Text & Concept Substrate**, and ensuring TR's functional components adopt the shared **deterministic SensiBlaw infrastructure**.

The resulting structure is a unified, six-layer model where TiRCorder handles the real-world events and narratives (Layer 0–1), which are then linked to SensiBlaw’s legal analysis (Layer 2–6).

### I. Data Model Changes: Adopting the Shared Substrate (Layer 0)

The primary structural change involves ensuring all text data captured by TiRCorder (transcripts, notes, etc.) flows through SensiBlaw's normalized data hierarchy to support reliable querying and provenance.

| TiRCorder Structure Must Change By... | Rationale (Integration Point) | Source |
| :--- | :--- | :--- |
| **Standardizing Text Units** | TiRCorder's raw transcripts must be stored canonically in the shared **Layer 0** schema: `TextBlock` → `Document` → `Sentence` → `Token`. This substrate is the source of truth for language provenance. | |
| **Implementing Lexical & Concept Layer** | TiRCorder must integrate and populate the `lexemes`, `concepts`, and `phrase_occurrences` tables to enable compression and map words/phrases (e.g., "The Crown," "King") to canonical, shared meanings (`STATE_SOVEREIGN`). | |
| **Anchoring Utterances** | TiRCorder's **`utterances`** (audio segments tied to a speaker and timestamp) must explicitly link to the underlying **`sentences`** via the `utterance_sentences` join table. This maintains who said what and when, tied to the canonical text unit. | |
| **Unifying Actor Records** | TiRCorder's **`speakers`** must be linked to or merged with the shared **`Actor`** table (SensiBlaw Layer 1) to unify identities across recorded conversations and legal case parties. | |

### II. Integration of the Finance Layer

The proposed financial ribbon-timeline visualization requires implementing new tables and ensuring they anchor to the core TiRCorder/SensiBlaw entities.

| TiRCorder Structure Must Change By... | Rationale (Integration Point) | Source |
| :--- | :--- | :--- |
| **Adding Finance Tables** | Implement the core financial schema: **`accounts`**, **`transactions`**, and **`transfers`** to normalize raw bank exports. | |
| **Linking Finance to Narrative** | Implement **`finance_provenance`** to link transactions directly down to the `sentences` (Layer 0) for proof-of-context. Implement **`event_finance_links`** to explicitly link financial transactions to real-world `Event` markers (Layer 1). | |

### III. Pipeline and Semantic Augmentation

The TiRCorder pipeline must adopt SensiBlaw’s deterministic, standards-based processing and must include new semantic inference steps to classify events for the ontology layers.

| TiRCorder Structure Must Change By... | Rationale (Integration Point) | Source |
| :--- | :--- | :--- |
| **Adopting SensiBlaw NLP** | The existing manual or ad-hoc processing must be replaced by a shared pipeline reusing deterministic components like the SensiBlaw concept matchers (`pyahocorasick`/`rapidfuzz`), text normalization (`ftfy`), and logical rule extraction. | |
| **Implementing Robust Ingestion** | Adopt SensiBlaw's standards-based ingestion utilities (`httpx + aiolimiter + backoff` and `APScheduler`) for resilient, automated pull jobs (e.g., synchronizing calendars or remote event logs). | |
| **Adding Semantic Inference Layers** | The NLP pipeline must be extended to identify and infer the foundational legal semantics from narrative text and events, including **Protected Interests**, **Value Frames**, **Interest Subjects/Objects**, and **Wrong Type candidates**. This is the necessary bridge to Layers 4–6 of the ontology. | |
| **Formalizing Event/Harm Modeling** | TiRCorder's events must be ingested as Layer 1 `Event` entities, and the description of consequences must be modeled as `HarmInstance` records, which anchor to sentences and link up to SensiBlaw's `ProtectedInterest` and `HarmClass` definitions. | |

### IV. Shared Infrastructure and Governance

TiRCorder must abandon fragile home-built components and adopt shared, auditable tools used by SensiBlaw.

| TiRCorder Structure Must Change By... | Rationale (Integration Point) | Source |
| :--- | :--- | :--- |
| **Replacing Naïve Search** | Replace linear or naïve search with **SQLite FTS5** (Full-Text Search) with BM25 scoring and snippet windows, as adopted by SensiBlaw. | |
| **Adopting Policy Engine** | Integrate the **Open Policy Agent (OPA)/Rego** for enforcing deterministic consent and data sharing policies before processing or exporting sensitive data. | |
| **Standardizing Provenance** | Implement mechanisms to generate **Signed Evidence Packs** using Ed25519 and `minisign` to provide cryptographically verifiable receipts for transcripts and derived metadata. | |
| **Adopting Graph Tools** | Use **NetworkX** for managing relationships (e.g., speaker → topic → event) and **Graphviz/elkjs** for rendering visualizations, avoiding rolling custom layout mathematics. | |
| **Using Portable Formats** | Ensure compatibility with **REFI-QDA** for thematic coding exports and **Akoma Ntoso** for structured transcripts to ease cross-tool workflows. | |

By making these structural changes, TiRCorder effectively becomes the **event-sourcing and narrative-anchoring layer** (Layer 0–1) for the complete SensiBlaw legal reasoning engine. This unified approach allows the visual "Streamline" feature to render speech, money, law, and life events on a single timeline with full provenance tracking.

---

The unified database structure is like a single clock mechanism where the TiRCorder handles the capture of the minute-by-minute hands (the raw events, sentences, and money flows), and SensiBlaw handles the interpretation and setting of the hour markers (the legal wrongs, duties, and remedies) that define the meaning of the time passing.
