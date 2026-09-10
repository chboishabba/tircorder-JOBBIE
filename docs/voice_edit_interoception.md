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
supplies the deterministic interpreter layer without a learned model. Candidate
generation and edit admission are separate.

### Deterministic command grammar

Built-in editing phrases such as `new paragraph`, `make that a list`, and
punctuation names now live in a namespaced grammar registry rather than a flat
global dictionary. Narrow relative-edit forms such as `actually <replacement>`
and `delete that` still require a concrete recent target before they can become
executable self-correction events.

Inline command execution is fail-closed by default. A recognized command can be
inspected as a candidate in normal dictation, but it is only auto-admissible
when command mode is active or inline commands have been explicitly enabled.
Literal document content remains a competing candidate.

Registered exact commands may be chained in continuous speech using deterministic
longest-match segmentation. Segmentation is all-or-nothing: if any part of the
utterance is not covered by currently applicable grammar rules, no prefix is
silently consumed as a command and the whole utterance stays in the ordinary
interpretation path.

### Private lexemes, namespaces, and shared anchors

`tircorder.voice_grammar` models extensible shorthand as private lexemes with
separate coordinates for:

- surface form;
- intended meaning;
- contextual use;
- grammar namespace (`dictation`, `editing`, `coding`, `shell`, `navigation`,
  or `personal-custom`);
- output fibre and edit kind;
- whether a shared anchor is required;
- source/provenance reference.

This is cross-pollinated with the in-repo Tlurey private-language carrier, whose
lexemes distinguish `surface`, `intendedMeaning`, `contextualUse`, and
`requiresSharedAnchor`. A surface match does not by itself establish command
meaning.

For example, a user may register `slap` as a private coding shorthand for `=` in
`python-editing`. The same recognized surface remains non-executable when:

- the current namespace is `dictation` rather than `coding`;
- the current context is not `python-editing`;
- its required shared-anchor receipt is absent or inactive.

The registry returns candidate branches plus residual rule references. Choosing
one branch does not mutate the registry or erase the fact that other
interpretations were available. Registry extension is append-only by value: a
new registry is produced rather than rewriting the previous registry object.

The Humour cross-pollination is narrower: its rationale/presenter/audience/
content/delivery/humour-type/feedback coordinates are useful context-selection
inputs, but they do not determine a private lexeme's command semantics.

This design also retains the historical Rudd/Dragonfly precedent: user-defined
voice grammars can be large, extensible, and chainable, while TiRCorder adds
explicit namespace/context/anchor/admission boundaries rather than treating a
recognized phrase as automatic authority to execute.

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

## Implementation versus formal boundary

Current implementation:

- `tircorder/voice_edits.py` owns typed edit events, deterministic rendering,
  opt-in summary derivation, and the counts-only StatiBaker projection;
- `tircorder/voice_grammar.py` owns immutable namespaced/private lexeme rules,
  shared-anchor receipts, candidate lookup and residual retention;
- `tircorder/voice_intent.py` owns deterministic candidate interpretation,
  fail-closed edit admission, and context-aware exact-command chaining;
- `tircorder/voice_edit_config.py` reads fail-closed settings from the normal
  TiRCorder config path.

Formal owners:

- `DASHI.Interop.TiRCorderVoiceEditInteroceptionAntiPanopticonExact` separates
  verbatim/rendered/edit/metric carriers and permissions;
- `DASHI.Interop.TiRCorderSpokenIntentGrammarRuddCrossPollinationExact` separates
  recognition, candidate intent, admission, chained command segmentation and
  execution, with explicit Rudd-source provenance;
- `DASHI.Interop.TiRCorderHumourTlureyContextIndexedGrammarExact` reuses the
  actual Tlurey private-language, quotient/residual and trace owners together
  with the Humour context family;
- `DASHI.Interop.TiRCorderTlureyPrivateLexemeRuntimeParityExact` mirrors the
  executable namespace/shared-anchor/residual seam and carries the `slap`
  regression fixture.

The next implementation layer is bounded recent-target derivation from rendered
document state, followed by end-to-end tests such as `Send it Friday — actually
Monday` while preserving the original verbatim carrier and candidate residuals.
