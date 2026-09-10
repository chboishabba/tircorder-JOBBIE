"""Typed voice-edit layer with opt-in, non-diagnostic self-observation.

This module deliberately sits *after* ASR.  Recognition produces a verbatim
transcript; a separate interpreter may emit :class:`VoiceEditEvent` objects;
and rendering applies those events without rewriting the verbatim carrier.

The optional metric surface is intentionally narrow.  It can count correction
and formatting events for personal reflection, but it does not infer intent,
health, competence, diagnosis, or a reason for the observed pattern.  A
StatiBaker projection is counts-only and requires a second explicit opt-in.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Iterable, Mapping, Sequence


class VoiceEditKind(str, Enum):
    INSERT = "insert"
    REPLACE_RECENT = "replace_recent"
    DELETE_RECENT = "delete_recent"
    PARAGRAPH_BREAK = "paragraph_break"
    LISTIFY = "listify"
    PUNCTUATE = "punctuate"
    FORMAT = "format"
    REWRITE_SELECTION = "rewrite_selection"
    LEARN_CORRECTION = "learn_correction"


class VoiceEditInterpretation(str, Enum):
    """Candidate semantic fibre assigned to recognized speech."""

    DOCUMENT_CONTENT = "document_content"
    SELF_CORRECTION = "self_correction"
    FORMATTING_COMMAND = "formatting_command"
    DISCOURSE_MARKER = "discourse_marker"
    QUOTED_SPEECH = "quoted_speech"
    ASR_ARTIFACT = "asr_artifact"
    UNRESOLVED = "unresolved"


@dataclass(frozen=True)
class VerbatimTranscript:
    text: str
    source_reference: str


@dataclass(frozen=True)
class VoiceEditEvent:
    event_id: str
    occurred_at: str
    kind: VoiceEditKind
    interpretation: VoiceEditInterpretation
    argument: str = ""
    replacement: str = ""
    source_span_reference: str = ""
    interpreter_reference: str = ""


@dataclass(frozen=True)
class RenderedTranscript:
    text: str
    verbatim_source_reference: str
    applied_event_ids: tuple[str, ...]


@dataclass(frozen=True)
class SelfObservationPolicy:
    """Explicit policy gate for a derived personal observation metric.

    ``enabled`` controls metric derivation.  ``share_with_statibaker`` is a
    distinct opt-in because observing a metric locally and exporting a metric
    summary are different consumer permissions.
    """

    enabled: bool = False
    purpose: str = "personal_interoceptive_reflection"
    share_with_statibaker: bool = False
    window_label: str = "session"


@dataclass(frozen=True)
class CorrectionMetricSummary:
    window_label: str
    event_count: int
    correction_count: int
    formatting_count: int
    content_count: int
    unresolved_count: int
    correction_fraction: float
    formatting_fraction: float
    purpose: str


def _replace_last(text: str, needle: str, replacement: str) -> str:
    if not needle:
        return text
    idx = text.rfind(needle)
    if idx < 0:
        return text
    return text[:idx] + replacement + text[idx + len(needle) :]


def _delete_last(text: str, needle: str) -> str:
    return _replace_last(text, needle, "")


def _listify(text: str) -> str:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if not lines:
        return text
    return "\n".join(line if line.startswith("- ") else f"- {line}" for line in lines)


def apply_voice_edits(
    verbatim: VerbatimTranscript,
    events: Sequence[VoiceEditEvent],
) -> RenderedTranscript:
    """Deterministically render an edit log over a verbatim transcript.

    The input ``VerbatimTranscript`` is immutable and is never modified.  This
    function consumes already-interpreted edit events; it does not infer that a
    word such as "actually" is necessarily a correction command.
    """

    text = verbatim.text
    applied: list[str] = []
    for event in events:
        if event.interpretation is VoiceEditInterpretation.UNRESOLVED:
            continue

        if event.kind is VoiceEditKind.INSERT:
            text += event.argument
        elif event.kind is VoiceEditKind.REPLACE_RECENT:
            text = _replace_last(text, event.argument, event.replacement)
        elif event.kind is VoiceEditKind.DELETE_RECENT:
            text = _delete_last(text, event.argument)
        elif event.kind is VoiceEditKind.PARAGRAPH_BREAK:
            text = text.rstrip() + "\n\n"
        elif event.kind is VoiceEditKind.LISTIFY:
            text = _listify(text)
        elif event.kind is VoiceEditKind.PUNCTUATE:
            punctuation = event.argument.strip()
            if punctuation and not text.rstrip().endswith(punctuation):
                text = text.rstrip() + punctuation
        elif event.kind in {
            VoiceEditKind.FORMAT,
            VoiceEditKind.REWRITE_SELECTION,
            VoiceEditKind.LEARN_CORRECTION,
        }:
            # These operations require an external formatter/editor/dictionary
            # consumer.  Their event is preserved, but this pure renderer does
            # not silently invent a transformation.
            continue
        else:  # pragma: no cover - Enum exhaustiveness guard
            continue
        applied.append(event.event_id)

    return RenderedTranscript(
        text=text,
        verbatim_source_reference=verbatim.source_reference,
        applied_event_ids=tuple(applied),
    )


def derive_correction_metric(
    events: Iterable[VoiceEditEvent],
    policy: SelfObservationPolicy,
) -> CorrectionMetricSummary | None:
    """Return an opt-in event summary, never a person-level score.

    No metric exists when the user-facing policy is disabled.  The result is a
    descriptive count/fraction over the selected event window only; it carries
    no diagnostic, normative, clinical, employment, legal, or competence
    semantics.
    """

    if not policy.enabled:
        return None

    materialized = tuple(events)
    n = len(materialized)
    correction = sum(
        event.interpretation is VoiceEditInterpretation.SELF_CORRECTION
        for event in materialized
    )
    formatting = sum(
        event.interpretation is VoiceEditInterpretation.FORMATTING_COMMAND
        for event in materialized
    )
    content = sum(
        event.interpretation is VoiceEditInterpretation.DOCUMENT_CONTENT
        for event in materialized
    )
    unresolved = sum(
        event.interpretation is VoiceEditInterpretation.UNRESOLVED
        for event in materialized
    )
    denom = n if n else 1
    return CorrectionMetricSummary(
        window_label=policy.window_label,
        event_count=n,
        correction_count=correction,
        formatting_count=formatting,
        content_count=content,
        unresolved_count=unresolved,
        correction_fraction=correction / denom,
        formatting_fraction=formatting / denom,
        purpose=policy.purpose,
    )


def statibaker_metric_signal(
    summary: CorrectionMetricSummary | None,
    policy: SelfObservationPolicy,
    *,
    observed_at: str | None = None,
) -> Mapping[str, object] | None:
    """Project an explicitly shared summary into StatiBaker's counts-only lane.

    Transcript text, spoken commands, source spans, and replacement strings are
    intentionally absent.  StatiBaker receives a structural observation, not a
    semantic judgement about the person who generated it.
    """

    if summary is None or not policy.enabled or not policy.share_with_statibaker:
        return None
    timestamp = observed_at or datetime.now(timezone.utc).isoformat()
    return {
        "ts": timestamp,
        "signal": "metric_summary",
        "metric": "tircorder_voice_edit_activity",
        "window": summary.window_label,
        "summary": {
            "events": summary.event_count,
            "corrections": summary.correction_count,
            "formatting_commands": summary.formatting_count,
            "unresolved": summary.unresolved_count,
            "correction_fraction": summary.correction_fraction,
            "formatting_fraction": summary.formatting_fraction,
        },
        "purpose": summary.purpose,
        "semantics": "observational_only_not_diagnostic_or_evaluative",
    }
