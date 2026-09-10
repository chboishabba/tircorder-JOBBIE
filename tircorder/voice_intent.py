"""Deterministic spoken-intent interpreter for TiRCorder.

This module intentionally contains no learned model.  It maps a small, pinned
command grammar into *candidate* voice-edit events.  Recognition remains an ASR
concern; this layer decides whether recognized words may be consumed as document
content or as an edit/control instruction.

The default policy is fail-closed for inline execution.  Exact command phrases
can be recognized in ordinary dictation, but they are only auto-admitted when
command mode is active or inline commands have been explicitly enabled.
Ambiguous discourse markers such as ``actually`` remain document content unless
they occur in the narrow correction form ``actually <replacement>`` and a
concrete recent target is available.
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
    """Return deterministic competing intent candidates for one utterance.

    Candidate generation and execution permission are separate.  Callers may
    inspect all candidates; :func:`admit_unique_candidate` performs the narrow
    policy gate for automatic execution.
    """

    raw = utterance.strip()
    text = _norm(raw)
    if not text:
        return ()

    out: list[VoiceIntentCandidate] = []

    # Ordinary document-content reading is always retained as a competing fibre.
    out.append(
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
    )

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


def admit_unique_candidate(
    candidates: Iterable[VoiceIntentCandidate],
    *,
    minimum_score: int = 90,
) -> VoiceEditEvent | None:
    """Admit one executable high-confidence non-content command, otherwise none.

    Literal document content is intentionally not auto-selected by this helper;
    the normal dictation path already owns content insertion.  This function is
    only the edit/control admission gate.
    """

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
