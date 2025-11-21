# TiRCorder connector contract

This document defines how TiRCorder connectors hand data to SensiBlaw. It covers
transport options, the ingestion hooks SensiBlaw will call, the normalized
payload shape, validation expectations, and examples for both file-based drops
and HTTP APIs.



* ❗ SensiBlaw handles *all* NLP, semantic extraction, concept mapping, rule atoms, ontology linking, contradiction detection, etc.
* ✔ TiRCorder handles *only* capture, diarisation, transcription, segmentation, provenance, and emitting structured utterance/events.
* ❗ The draft you pasted was actually the *legal-graph ingestion* contract — not the TiRCorder one.
* ✔ Below is the **correct** contract specifically for TiRCorder’s role in ITIR → SL ingestion.

---

# ✅ **TiRCorder → SensiBlaw Connector Contract**

This contract defines precisely what **TiRCorder must emit**, how it does so, and how **SensiBlaw consumes** these packets.
It is intentionally scoped to match the ITIR/SensiBlaw architecture:

* TiRCorder = **recording + diarisation + transcription + provenance**
* SensiBlaw = **text substrate + NLP + ontology + actors + events + legal logic**

Everything below keeps that separation strict.

---

# 1. Overview

A TiRCorder connector hands structured recordings into SensiBlaw using a **NormalizedTiRCEventPacket**.
This packet:

* contains *zero* semantics
* contains *zero* NLP preprocessing
* contains *zero* ontology logic
* carries only **utterances**, **timestamps**, **speaker labels**, **provenance**, **audio hashes**, **sentence splits**, and optional **audio analytics**

SensiBlaw then:

* creates documents, sentences, tokens
* resolves actors
* attaches sentences to events
* performs NLP, semantic triggers, concept detection
* integrates into Streamline/Timeline
* performs rule extraction, harm/wrong detection, etc.

---

# 2. Transport Options

TiRCorder connectors may deliver packets via either:

## **A. Local file drops (preferred for backfills)**

* Write to: `data/tircorder/<connector_name>/`
* Format: `*.ndjson` or single JSON file
* Each line/file = one `NormalizedTiRCEventPacket`

SensiBlaw calls:

```python
load_from_path(path: Path) -> NormalizedTiRCEventPacket
```

Atomic write requirement:

* Write to `tmpfile`
* Then rename to final name

Prevents partial reads.

---

## **B. HTTP ingestion (for live/streaming feeds)**

POST to:

```
POST /api/ingestion/tircorder
```

GET healthcheck:

```
GET /api/ingestion/tircorder/health
```

Cursor-based pagination for streamers:

```python
fetch_since(cursor: Optional[str]) -> NormalizedTiRCEventPacket
```

Auth: Bearer token.

---

# 3. The **Normalized TiRC Event Packet** (Final Schema)

This is the canonical payload **TiRCorder MUST emit**.

⚠️ **No NLP tokens, no semantic labels, no concepts, no edges, no nodes.**
These belong to SensiBlaw.

---

# ✅ **TiRCorder Payload Schema (final)**

```json
{
  "connector": "tircorder",
  "batch_id": "2025-02-15T12:33:44Z",
  "ingested_at": "2025-02-15T12:33:44Z",

  "source": {
    "origin": "tircorder-device-id",
    "contact": "device-owner-or-operator"
  },

  "cursor": null,
  "next_cursor": null,

  "sessions": [
    {
      "session_id": "sess-4412",
      "device_id": "ABC-123",
      "started_at": "ISO-8601",
      "ended_at":   "ISO-8601",
      "audio_sha256": "hash-of-raw-audio-file",

      "utterances": [
        {
          "utterance_id": "utt-1",
          "start": "ISO-8601",
          "end":   "ISO-8601",

          "speaker_label": "SPEAKER_1",
          "speaker_confidence": 0.94,

          "text": "full utterance text",

          "words": [
            { "w": "hello", "start": 1.23, "end": 1.44, "conf": 0.98 }
          ],

          "silence_before": 0.8,
          "silence_after": 0.3,
          "energy": 0.62,

          "sentence_splits": [
            { "char_start": 0, "char_end": 22 },
            { "char_start": 23, "char_end": 32 }
          ]
        }
      ],

      "segments": [
        { "start": 0.0, "end": 2.1, "type": "speech" },
        { "start": 2.1, "end": 4.5, "type": "silence" }
      ],

      "analytics": {
        "emotion": "neutral",
        "sentiment": 0.1,
        "pitch_contour": [],
        "vad_energy": []
      }
    }
  ],

  "raw_payload": {}
}
```

---

# 4. What TiRCorder MUST Emit

### Required:

| Field                                | Why                                             |
| ------------------------------------ | ----------------------------------------------- |
| **audio hash**                       | provenance & tamper-evidence                    |
| **timestamps (segment & utterance)** | timeline anchoring                              |
| **utterance text**                   | SL creates sentences/tokens                     |
| **speaker_label**                    | actor alias resolution                          |
| **device/session metadata**          | identity + chain-of-custody                     |
| **sentence_splits**                  | sentence table seeding                          |
| **word timings**                     | improves timeline overlay, FTS snippet accuracy |
| **segments (speech/silence)**        | Streamline ribbon overlays                      |

---

# 5. What TiRCorder MAY Emit

Optional enhancements:

* VAD energy time series
* Pitch/emotion
* Word-level confidence
* Noise events
* Structured markers (cough, bang, door slam)
* Overlapping speakers (if diariser supports it)

---

# 6. What TiRCorder MUST NOT Emit

❌ NLP tokens
❌ lemmas
❌ POS tags
❌ dependency labels
❌ concept triggers
❌ legal edges or nodes
❌ rule atoms
❌ harm/wrong classifications
❌ actor canonical IDs
❌ event types beyond basic “utterance”

These belong **exclusively** to SensiBlaw.

---

# 7. How SensiBlaw Consumes This Payload

SensiBlaw converts the above into:

| SensiBlaw Table    | Data from TiRCorder             |
| ------------------ | ------------------------------- |
| `documents`        | session transcript text         |
| `sentences`        | from `sentence_splits`          |
| `tokens`           | SensiBlaw NLP                   |
| `utterances`       | from `utterances[*]`            |
| `events`           | event_kind=SPEECH               |
| `event_provenance` | timestamps + audio hash         |
| `actor_aliases`    | using speaker_label             |
| `audio_features`   | from analytics                  |
| `timeline_events`  | mapped from utterance start/end |

This locks perfectly into:

* Streamline ribbons
* Event overlays
* Cross-linking with finance
* Graph nodes (event nodes)
* Claims/case analysis
* Harm/wrong inference
* ReceiptPack generation

---

# 7.1 Handoff to SensiBlaw

1. TiRCorder writes or POSTs a **NormalizedTiRCEventPacket** (sections 2–5 above).
2. SensiBlaw’s ingestion layer (`sensiblaw.connectors.tircorder`) validates the packet and maps it into the text substrate (documents + sentences + utterances) described in `docs/ITIR - SL - DB_god_doc.md`.
3. Downstream SL pipelines (NLP, actor resolution, legal graphing) attach semantics onto those text anchors; TiRCorder does not emit nodes/edges/events/documents itself.

This keeps TiRCorder focused on capture/provenance while SL owns all higher-level semantics.

---

# 8. Validation Rules (Final)

SensiBlaw enforces:

1. **connector**, **batch_id**, **ingested_at**, **sessions** required
2. utterances require at minimum:

   * `utterance_id`, `start`, `end`, `text`, `speaker_label`
3. all timestamps ISO-8601
4. audio hashes must be hex SHA-256
5. word timings must be monotonic
6. sentence_splits must map to character offsets inside `text`

All validation happens before any DB write.

---

# 9. Idempotency

* Same `{connector,batch_id}` + same content → **no-op**
* Same batch_id + *different* content → **409** error
* SensiBlaw merges speaker labels across batches
* SensiBlaw deduplicates event anchors by `(session_id, utterance_id)`

---

# 10. Sample `.ndjson`

```jsonl
{"connector":"tircorder","batch_id":"2025-02-10T11:12:33Z","ingested_at":"2025-02-10T11:12:33Z","source":{"origin":"android-device","contact":"user@example"},"sessions":[{"session_id":"sess-99","device_id":"XYZ","started_at":"2025-02-10T10:00:00Z","ended_at":"2025-02-10T11:00:00Z","audio_sha256":"abc123...","utterances":[{"utterance_id":"utt-1","start":"2025-02-10T10:10:11Z","end":"2025-02-10T10:10:13Z","speaker_label":"S1","text":"I can't keep doing this.","words":[{"w":"I","start":11.1,"end":11.2},{"w":"can't","start":11.2,"end":11.5}],"sentence_splits":[{"char_start":0,"char_end":20}]}]}]}
```

---

# 11. Summary (TL;DR)

**TiRCorder emits only:**

* audio metadata
* timestamps
* utterances
* sentence boundaries
* diarisation labels
* audio analytics

**SensiBlaw handles everything semantic**, including:

* NLP
* actor mapping
* event creation
* claims
* harms
* wrongs
* rule atoms
* graphs
* timeline visualisation

This ensures **clean separation**, high auditability, and full reproducibility.
