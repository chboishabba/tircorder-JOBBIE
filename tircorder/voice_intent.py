"""Deterministic spoken-intent interpreter for TiRCorder.

This module intentionally contains no learned model. It maps recognized speech
into candidate voice-edit fibres through a pinned, namespaced grammar registry.
Recognition, surface match, contextual meaning, admission and execution remain
distinct coordinates.

Private/custom lexemes may require a shared-anchor receipt. Candidate generation
retains competing interpretations and residual rule references. Continuous
command chains use deterministic longest-match segmentation and only segment an
utterance when the entire utterance is covered by currently applicable grammar
rules; otherwise the utterance stays intact.
"""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Iterable

from .voice_edits import VoiceEditEvent, VoiceEditInterpretation, VoiceEditKind
from .voice_grammar import (
    BUILTIN_EDITING_GRAMMAR,
    GrammarNamespace,
    GrammarRegistry,
    SharedAnchorReceipt,
)

INTERPRETER_REFERENCE = "tircorder.voice_intent.rule-v2"


@dataclass(frozen=True)
class VoiceIntentPolicy:
    command_mode: bool = False
    allow_inline_commands: bool = False
    namespace: GrammarNamespace = GrammarNamespace.EDITING


@dataclass(frozen=True)
class VoiceIntentContext:
    source_span_reference: str
    recent_target: str = ""
    selection_active: bool = False
    context_reference: str = ""
    shared_anchor: SharedAnchorReceipt | None = None


@dataclass(frozen=True)
class VoiceIntentCandidate:
    event: VoiceEditEvent
    score: int
    rationale: str
    executable_under_policy: bool
    grammar_rule_reference: str = ""
    residual_reference: str = ""


@dataclass(frozen=True)
class VoiceIntentSegment:
    index: int
    utterance: str
    candidates: tuple[VoiceIntentCandidate, ...]


def _norm(text: str) -> str:
    return " ".join(text.strip().lower().split())


def _event(
    *,
    event_id: str,
    kind: VoiceEditKind,
    interpretation: VoiceEditInterpretation,
    context: VoiceIntentContext,
    argument: str = "",
    replacement: str = "",
) -> VoiceEditEvent:
    return VoiceEditEvent(
        event_id=event_id,
        occurred_at="",
        kind=kind,
        interpretation=interpretation,
        argument=argument,
        replacement=replacement,
        source_span_reference=context.source_span_reference,
        interpreter_reference=INTERPRETER_REFERENCE,
    )


def _command_executable(policy: VoiceIntentPolicy) -> bool:
    return policy.command_mode or policy.allow_inline_commands


def interpret_utterance(
    utterance: str,
    *,
    event_id: str,
    context: VoiceIntentContext,
    policy: VoiceIntentPolicy = VoiceIntentPolicy(),
    registry: GrammarRegistry = BUILTIN_EDITING_GRAMMAR,
) -> tuple[VoiceIntentCandidate, ...]:
    """Return deterministic competing intent candidates for one utterance."""

    raw = utterance.strip()
    text = _norm(raw)
    if not text:
        return ()

    out: list[VoiceIntentCandidate] = [
        VoiceIntentCandidate(
            event=_event(
                event_id=f"{event_id}:content",
                kind=VoiceEditKind.INSERT,
                interpretation=VoiceEditInterpretation.DOCUMENT_CONTENT,
                context=context,
                argument=raw,
            ),
            score=20,
            rationale="recognized speech may be literal document content",
            executable_under_policy=True,
        )
    ]

    lookup = registry.lookup(
        raw,
        namespace=policy.namespace,
        context_reference=context.context_reference,
        anchor=context.shared_anchor,
    )
    residual_ref = "|".join(lookup.residual_surfaces)
    for branch in lookup.candidates:
        out.append(
            VoiceIntentCandidate(
                event=_event(
                    event_id=f"{event_id}:grammar:{branch.rule.rule_id}",
                    kind=branch.rule.output_kind,
                    interpretation=branch.rule.output_fibre,
                    context=context,
                    argument=branch.rule.argument,
                ),
                score=branch.candidate_score,
                rationale=branch.rationale,
                executable_under_policy=(
                    branch.anchor_satisfied
                    and branch.context_satisfied
                    and _command_executable(policy)
                ),
                grammar_rule_reference=branch.rule.rule_id,
                residual_reference=residual_ref,
            )
        )

    correction = re.fullmatch(r"actually\s+(.+)", text)
    if correction:
        replacement = raw.split(None, 1)[1].strip()
        if context.recent_target:
            out.append(
                VoiceIntentCandidate(
                    event=_event(
                        event_id=f"{event_id}:correction",
                        kind=VoiceEditKind.REPLACE_RECENT,
                        interpretation=VoiceEditInterpretation.SELF_CORRECTION,
                        context=context,
                        argument=context.recent_target,
                        replacement=replacement,
                    ),
                    score=95,
                    rationale="correction marker plus explicit recent target",
                    executable_under_policy=_command_executable(policy),
                )
            )
        else:
            out.append(
                VoiceIntentCandidate(
                    event=_event(
                        event_id=f"{event_id}:unresolved-correction",
                        kind=VoiceEditKind.REPLACE_RECENT,
                        interpretation=VoiceEditInterpretation.UNRESOLVED,
                        context=context,
                        replacement=replacement,
                    ),
                    score=80,
                    rationale="correction form recognized but no concrete recent target",
                    executable_under_policy=False,
                )
            )

    if text in {"delete that", "no delete that", "no, delete that"}:
        if context.recent_target:
            out.append(
                VoiceIntentCandidate(
                    event=_event(
                        event_id=f"{event_id}:delete",
                        kind=VoiceEditKind.DELETE_RECENT,
                        interpretation=VoiceEditInterpretation.SELF_CORRECTION,
                        context=context,
                        argument=context.recent_target,
                    ),
                    score=95,
                    rationale="delete command plus explicit recent target",
                    executable_under_policy=_command_executable(policy),
                )
            )
        else:
            out.append(
                VoiceIntentCandidate(
                    event=_event(
                        event_id=f"{event_id}:unresolved-delete",
                        kind=VoiceEditKind.DELETE_RECENT,
                        interpretation=VoiceEditInterpretation.UNRESOLVED,
                        context=context,
                    ),
                    score=80,
                    rationale="delete command recognized but target is unresolved",
                    executable_under_policy=False,
                )
            )

    if text.startswith("make this ") or text.startswith("make that "):
        instruction = raw.split(None, 2)[2].strip() if len(raw.split(None, 2)) == 3 else ""
        if instruction and context.selection_active:
            out.append(
                VoiceIntentCandidate(
                    event=_event(
                        event_id=f"{event_id}:format-selection",
                        kind=VoiceEditKind.FORMAT,
                        interpretation=VoiceEditInterpretation.FORMATTING_COMMAND,
                        context=context,
                        argument=instruction,
                    ),
                    score=90,
                    rationale="format instruction with active selection",
                    executable_under_policy=_command_executable(policy),
                )
            )

    return tuple(sorted(out, key=lambda c: (-c.score, c.event.event_id)))


def _applicable_exact_surfaces(
    registry: GrammarRegistry,
    *,
    policy: VoiceIntentPolicy,
    context: VoiceIntentContext,
) -> tuple[str, ...]:
    surfaces: list[str] = []
    for rule in registry.rules:
        lookup = registry.lookup(
            rule.surface,
            namespace=policy.namespace,
            context_reference=context.context_reference,
            anchor=context.shared_anchor,
        )
        if any(
            branch.rule.rule_id == rule.rule_id
            and branch.anchor_satisfied
            and branch.context_satisfied
            for branch in lookup.candidates
        ):
            surfaces.append(_norm(rule.surface))
    return tuple(sorted(set(surfaces)))


def _segment_exact_command_chain(
    text: str,
    *,
    policy: VoiceIntentPolicy,
    context: VoiceIntentContext,
    registry: GrammarRegistry,
) -> tuple[str, ...] | None:
    """Cover text completely with currently applicable rules, longest-first."""

    words = _norm(text).split()
    if not words:
        return ()
    phrases = sorted(
        ((phrase.split(), phrase) for phrase in _applicable_exact_surfaces(
            registry, policy=policy, context=context
        )),
        key=lambda item: (-len(item[0]), item[1]),
    )
    out: list[str] = []
    i = 0
    while i < len(words):
        match: tuple[list[str], str] | None = None
        for phrase_words, phrase in phrases:
            n = len(phrase_words)
            if words[i : i + n] == phrase_words:
                match = (phrase_words, phrase)
                break
        if match is None:
            return None
        phrase_words, phrase = match
        out.append(phrase)
        i += len(phrase_words)
    return tuple(out)


def interpret_command_chain(
    utterance: str,
    *,
    event_id: str,
    context: VoiceIntentContext,
    policy: VoiceIntentPolicy = VoiceIntentPolicy(),
    registry: GrammarRegistry = BUILTIN_EDITING_GRAMMAR,
) -> tuple[VoiceIntentSegment, ...]:
    """Interpret a fully covered continuous command chain deterministically."""

    chain = _segment_exact_command_chain(
        utterance,
        policy=policy,
        context=context,
        registry=registry,
    )
    if chain is None or len(chain) <= 1:
        return (
            VoiceIntentSegment(
                index=0,
                utterance=utterance.strip(),
                candidates=interpret_utterance(
                    utterance,
                    event_id=event_id,
                    context=context,
                    policy=policy,
                    registry=registry,
                ),
            ),
        )
    return tuple(
        VoiceIntentSegment(
            index=i,
            utterance=phrase,
            candidates=interpret_utterance(
                phrase,
                event_id=f"{event_id}:segment:{i}",
                context=context,
                policy=policy,
                registry=registry,
            ),
        )
        for i, phrase in enumerate(chain)
    )


def admit_unique_candidate(
    candidates: Iterable[VoiceIntentCandidate],
    *,
    minimum_score: int = 90,
) -> VoiceEditEvent | None:
    """Admit one executable high-confidence non-content command, otherwise none."""

    eligible = [
        c
        for c in candidates
        if c.executable_under_policy
        and c.score >= minimum_score
        and c.event.interpretation
        in {
            VoiceEditInterpretation.SELF_CORRECTION,
            VoiceEditInterpretation.FORMATTING_COMMAND,
        }
    ]
    if len(eligible) != 1:
        return None
    return eligible[0].event
