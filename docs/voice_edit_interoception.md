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

The interpreter should keep competing semantic interpretations available when
necessary.  A token such as `actually` may be a self-correction command, an
ordinary discourse marker, quoted speech, or an ASR artefact.  Unresolved intent
must not execute automatically.

`tircorder.voice_edits` consumes already-interpreted events; it deliberately
does not implement a regex command recognizer.

## Personal correction-activity metric

Correction/formatting frequency can optionally be surfaced as a descriptive
self-observation coordinate.  The intended use is personal reflection: a user
may decide that noticing changes in their own correction activity is useful
context.  The metric does **not** encode why the rate changed.

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

Enabling the local metric does not enable downstream sharing.  StatiBaker
sharing is a separate opt-in.

## StatiBaker boundary

When explicitly enabled for StatiBaker, TiRCorder emits only a structural
`metric_summary` projection containing counts/fractions.  It does not include:

- transcript text;
- correction text;
- replacement text;
- source spans.

This follows StatiBaker's existing observed-signal discipline: observed signals
are append-only structural context, not semantic authority; drift is a signal,
not diagnosis, scoring, prioritization, or automation.

Turning metric collection off stops future metric derivation/export.  It does
not rewrite source audio, verbatim transcripts, or the historical edit ledger.

## Implementation versus ideal formal boundary

Current implementation:

- `tircorder/voice_edits.py` owns typed edit events, deterministic rendering,
  opt-in summary derivation, and the counts-only StatiBaker projection;
- `tircorder/voice_edit_config.py` reads fail-closed settings from the normal
  TiRCorder config path;
- the existing TiRCorder downstream path remains responsible for transcript
  artifacts and suite fan-out.

Formal ideal:

- `DASHI.Interop.TiRCorderVoiceEditInteroceptionAntiPanopticonExact` in
  `dashi_agda` separates verbatim/rendered/edit/metric carriers, makes metric
  derivation and external export separately permissioned, and blocks promotion
  of descriptive correction activity into diagnosis, competence scoring,
  surveillance authority, or intervention authority.

The next implementation layer is the actual speech-intent interpreter and UI.
It should feed the typed event carrier rather than editing transcript evidence
in place.
