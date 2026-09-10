"""Deterministic spoken-intent interpreter for TiRCorder.

This module intentionally contains no learned model. It maps a small, pinned
command grammar into *candidate* voice-edit events. Recognition remains an ASR
concern; this layer decides whether recognized words may be consumed as document
content or as an edit/control instruction.

The default policy is fail-closed for inline execution. Exact command phrases
can be recognized in ordinary dictation, but they are only auto-admitted when
command mode is active or inline commands have been explicitly enabled.
Ambiguous discourse markers such as ``actually`` remain document content unless
they occur in the narrow correction form ``actually <replacement>`` and a
concrete recent target is available.

A second entry point, :func:`interpret_command_chain`, supports the historical
Dragonfly/Rudd idea that several registered commands may be spoken continuously.
It uses deterministic longest-match segmentation and only segments an utterance
when the *entire* utterance can be covered by registered exact command phrases;
otherwise the utterance stays intact for ordinary candidate interpretation.
"""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Iterable

from .voice_edits import VoiceEditEvent, VoiceEditInterpretation, VoiceEditKind

INTERPRETER_REFERENCE = "tircorder.voice_intent.rule-v1"


@dataclass(frozen=True)
class VoiceIntentPolicy:
    command_mode: bool = False
    allow_inline_commands: bool = False


@dataclass(frozen=True)
class VoiceIntentContext:
    source_span_reference: str
    recent_target: str = ""
    selection_active: bool = False


@dataclass(frozen=True)
class VoiceIntentCandidate:
    event: VoiceEditEvent
    score: int
    rationale: str
    executable_under_policy: bool


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


_EXACT_COMMANDS: dict[str, tuple[VoiceEditKind, str]] = {
    "new paragraph": (VoiceEditKind.PARAGRAPH_BREAK, ""),
    "paragraph break": (VoiceEditKind.PARAGRAPH_BREAK, ""),
    "make that a list": (VoiceEditKind.LISTIFY, ""),
    "listify": (VoiceEditKind.LISTIFY, ""),
    "comma": (VoiceEditKind.PUNCTUATE, ","),
    "full stop": (VoiceEditKind.PUNCTUATE, "."),
    "period": (VoiceEditKind.PUNCTUATE, "."),
    "question mark": (VoiceEditKind.PUNCTUATE, "?"),
    "colon": (VoiceEditKind.PUNCTUATE, ":"),
    "semicolon": (VoiceEditKind.PUNCTUATE, ";"),
}


def interpret_utterance(
    utterance: str,
    *,
    event_id: str,
    context: VoiceIntentContext,
    policy: VoiceIntentPolicy = VoiceIntentPolicy(),
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

    if text in _EXACT_COMMANDS:
        kind, argument = _EXACT_COMMANDS[text]
        out.append(
            VoiceIntentCandidate(
                event=_event(
                    event_id=f"{event_id}:command",
                    kind=kind,
                    interpretation=VoiceEditInterpretation.FORMATTING_COMMAND,
                    context=context,
                    argument=argument,
                ),
                score=100,
                rationale="exact pinned formatting-command phrase",
                executable_under_policy=_command_executable(policy),
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


def _segment_exact_command_chain(text: str) -> tuple[str, ...] | None:
    """Cover ``text`` completely with registered commands using longest match."""

    words = _norm(text).split()
    if not words:
        return ()
    phrases = sorted(
        ((phrase.split(), phrase) for phrase in _EXACT_COMMANDS),
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
) -> tuple[VoiceIntentSegment, ...]:
    """Interpret a fully registered continuous command chain deterministically.

    If any part of the utterance is not covered by the exact grammar, the whole
    utterance is returned as one segment. This prevents partial grammar matches
    from silently consuming nearby document content.
    """

    chain = _segment_exact_command_chain(utterance)
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
