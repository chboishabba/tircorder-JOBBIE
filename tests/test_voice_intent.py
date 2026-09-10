from tircorder.voice_edits import VoiceEditInterpretation, VoiceEditKind
from tircorder.voice_intent import (
    VoiceIntentContext,
    VoiceIntentPolicy,
    admit_unique_candidate,
    interpret_utterance,
)


def ctx(**kwargs):
    return VoiceIntentContext(source_span_reference="span:test", **kwargs)


def test_exact_formatting_command_is_detected_but_fail_closed_by_default():
    candidates = interpret_utterance("new paragraph", event_id="e1", context=ctx())
    command = next(c for c in candidates if c.event.interpretation is VoiceEditInterpretation.FORMATTING_COMMAND)
    assert command.event.kind is VoiceEditKind.PARAGRAPH_BREAK
    assert command.score == 100
    assert command.executable_under_policy is False
    assert admit_unique_candidate(candidates) is None


def test_command_mode_admits_exact_formatting_command():
    candidates = interpret_utterance(
        "new paragraph",
        event_id="e2",
        context=ctx(),
        policy=VoiceIntentPolicy(command_mode=True),
    )
    admitted = admit_unique_candidate(candidates)
    assert admitted is not None
    assert admitted.kind is VoiceEditKind.PARAGRAPH_BREAK
    assert admitted.interpretation is VoiceEditInterpretation.FORMATTING_COMMAND


def test_actually_in_ordinary_sentence_is_not_a_correction_command():
    candidates = interpret_utterance(
        "I actually like Friday",
        event_id="e3",
        context=ctx(recent_target="Friday"),
        policy=VoiceIntentPolicy(command_mode=True),
    )
    assert all(c.event.interpretation is not VoiceEditInterpretation.SELF_CORRECTION for c in candidates)
    assert admit_unique_candidate(candidates) is None


def test_actually_replacement_requires_explicit_recent_target():
    no_target = interpret_utterance(
        "actually Monday",
        event_id="e4",
        context=ctx(),
        policy=VoiceIntentPolicy(command_mode=True),
    )
    unresolved = next(c for c in no_target if c.event.interpretation is VoiceEditInterpretation.UNRESOLVED)
    assert unresolved.executable_under_policy is False
    assert admit_unique_candidate(no_target) is None

    with_target = interpret_utterance(
        "actually Monday",
        event_id="e5",
        context=ctx(recent_target="Friday"),
        policy=VoiceIntentPolicy(command_mode=True),
    )
    admitted = admit_unique_candidate(with_target)
    assert admitted is not None
    assert admitted.kind is VoiceEditKind.REPLACE_RECENT
    assert admitted.argument == "Friday"
    assert admitted.replacement == "Monday"


def test_delete_that_requires_target_and_command_permission():
    candidates = interpret_utterance(
        "delete that",
        event_id="e6",
        context=ctx(recent_target="wrong words"),
    )
    assert admit_unique_candidate(candidates) is None

    candidates = interpret_utterance(
        "delete that",
        event_id="e7",
        context=ctx(recent_target="wrong words"),
        policy=VoiceIntentPolicy(allow_inline_commands=True),
    )
    admitted = admit_unique_candidate(candidates)
    assert admitted is not None
    assert admitted.kind is VoiceEditKind.DELETE_RECENT
    assert admitted.argument == "wrong words"


def test_hyphen_or_weird_vocabulary_is_not_special_without_registered_grammar():
    candidates = interpret_utterance(
        "slap jive message string",
        event_id="e8",
        context=ctx(),
        policy=VoiceIntentPolicy(command_mode=True),
    )
    assert len(candidates) == 1
    assert candidates[0].event.interpretation is VoiceEditInterpretation.DOCUMENT_CONTENT
    assert admit_unique_candidate(candidates) is None
