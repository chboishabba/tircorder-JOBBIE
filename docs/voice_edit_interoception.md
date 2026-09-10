# Voice edits and opt-in self-observation

TiRCorder distinguishes four carriers that should not be collapsed:

1. **verbatim transcript** — what the ASR/transcript producer emitted;
2. **voice edit ledger** — interpreted correction/formatting operations;
3. **rendered transcript** — a deterministic projection of the verbatim carrier plus admitted edits;
4. **optional self-observation metric** — counts/fractions derived only when explicitly enabled.

This is the important architectural difference between improving a dictation UX
and silently rewriting source evidence.

## Flow-like editing

A downstream voice-edit interpreter may emit typed operations such as:

- replace recent text;
- delete recent text;
- insert text;
- paragraph break;
- list formatting;
- punctuation;
- format/rewrite selection;
- learn a persistent correction.

The interpreter keeps competing semantic interpretations available when
necessary. A token such as `actually` may be a self-correction command, an
ordinary discourse marker, quoted speech, or an ASR artefact. Unresolved intent
must not execute automatically.

`tircorder.voice_edits` consumes interpreted events. `tircorder.voice_intent`
now supplies the first deterministic interpreter layer without any learned
model. Candidate generation and edit admission are separate.

### Deterministic command grammar

The initial grammar recognizes a deliberately small set of pinned phrases such
as `new paragraph`, `make that a list`, and punctuation names. It also recognizes
narrow relative-edit forms such as `actually <replacement>` and `delete that`,
but those require a concrete recent target before they can become executable
self-correction events.

Inline command execution is fail-closed by default. A recognized command can be
inspected as a candidate in normal dictation, but it is only auto-admissible
when command mode is active or inline commands have been explicitly enabled.
Literal document content remains a competing candidate.

Registered exact commands may be chained in continuous speech using deterministic
longest-match segmentation. Segmentation is all-or-nothing: if any part of the
utterance is not covered by the exact grammar, no prefix is silently consumed as
a command and the whole utterance stays in the ordinary interpretation path.

This design is cross-pollinated with Tavis Rudd's *Using Python to Code by Voice*
(PyCon US 2013). Rudd described Dragonfly grammars as mappings from things one
might say to actions the computer should perform, used a large user-extensible
command vocabulary, and later noted that many commands could be chained in
continuous speech. TiRCorder adopts that compositional grammar idea, not Rudd's
specific command vocabulary or an assumption that grammar recognition proves
speaker intent.

## Personal correction-activity metric

Correction/formatting frequency can optionally be surfaced as a descriptive
self-observation coordinate. The intended use is personal reflection: a user
may decide that noticing changes in their own correction activity is useful
context. The metric does **not** encode why the rate changed.

It is not:

- a fluency or competence score;
- a diagnosis;
- evidence of impairment;
- a semantic label for what the user was doing;
- a trigger for automated intervention.

The metric defaults to disabled.

Example `~/.tircorder/config.json` fragment:

```json
{
  "voice_edit": {
    "self_observation": {
      "enabled": true,
      "window": "session",
      "purpose": "personal_interoceptive_reflection",
      "share_with_statibaker": false
    }
  }
}
```

Enabling the local metric does not enable downstream sharing. StatiBaker
sharing is a separate opt-in.

## StatiBaker boundary

When explicitly enabled for StatiBaker, TiRCorder emits only a structural
`metric_summary` projection containing counts/fractions. It does not include:

- transcript text;
- correction text;
- replacement text;
- source spans.

This follows StatiBaker's existing observed-signal discipline: observed signals
are append-only structural context, not semantic authority; drift is a signal,
not diagnosis, scoring, prioritization, or automation.

Turning metric collection off stops future metric derivation/export. It does
not rewrite source audio, verbatim transcripts, or the historical edit ledger.

## Implementation versus ideal formal boundary

Current implementation:

- `tircorder/voice_edits.py` owns typed edit events, deterministic rendering,
  opt-in summary derivation, and the counts-only StatiBaker projection;
- `tircorder/voice_intent.py` owns deterministic candidate interpretation,
  fail-closed edit admission, and exact-command chaining;
- `tircorder/voice_edit_config.py` reads fail-closed settings from the normal
  TiRCorder config path;
- the existing TiRCorder downstream path remains responsible for transcript
  artifacts and suite fan-out.

Formal ideal:

- `DASHI.Interop.TiRCorderVoiceEditInteroceptionAntiPanopticonExact` separates
  verbatim/rendered/edit/metric carriers and permissions;
- `DASHI.Interop.TiRCorderSpokenIntentGrammarRuddCrossPollinationExact` separates
  recognition, candidate intent, admission, chained command segmentation and
  execution, with explicit Rudd-source provenance.

The next implementation layer is UI/runtime wiring: obtain a bounded recent
edit target from the rendered-document state, feed recognized utterances through
`tircorder.voice_intent`, display unresolved competing fibres when necessary,
and append only admitted `VoiceEditEvent`s to the edit ledger.
