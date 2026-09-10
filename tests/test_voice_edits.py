from tircorder.voice_edits import (
    SelfObservationPolicy,
    VerbatimTranscript,
    VoiceEditEvent,
    VoiceEditInterpretation,
    VoiceEditKind,
    apply_voice_edits,
    derive_correction_metric,
    statibaker_metric_signal,
)


def event(event_id, kind, interpretation, argument="", replacement=""):
    return VoiceEditEvent(
        event_id=event_id,
        occurred_at="2026-09-11T00:00:00Z",
        kind=kind,
        interpretation=interpretation,
        argument=argument,
        replacement=replacement,
        source_span_reference=f"span:{event_id}",
        interpreter_reference="test",
    )


def test_rendered_transcript_changes_without_rewriting_verbatim():
    verbatim = VerbatimTranscript("Send it Friday", "audio:1")
    correction = event(
        "e1",
        VoiceEditKind.REPLACE_RECENT,
        VoiceEditInterpretation.SELF_CORRECTION,
        "Friday",
        "Monday",
    )
    rendered = apply_voice_edits(verbatim, [correction])
    assert verbatim.text == "Send it Friday"
    assert rendered.text == "Send it Monday"
    assert rendered.applied_event_ids == ("e1",)


def test_unresolved_interpretation_is_not_silently_executed():
    verbatim = VerbatimTranscript("I actually like Friday", "audio:2")
    unresolved = event(
        "e2",
        VoiceEditKind.DELETE_RECENT,
        VoiceEditInterpretation.UNRESOLVED,
        "Friday",
    )
    rendered = apply_voice_edits(verbatim, [unresolved])
    assert rendered.text == verbatim.text
    assert rendered.applied_event_ids == ()


def test_metric_is_absent_without_explicit_opt_in():
    events = [
        event("e1", VoiceEditKind.REPLACE_RECENT, VoiceEditInterpretation.SELF_CORRECTION)
    ]
    assert derive_correction_metric(events, SelfObservationPolicy(enabled=False)) is None


def test_metric_is_descriptive_when_enabled():
    events = [
        event("e1", VoiceEditKind.REPLACE_RECENT, VoiceEditInterpretation.SELF_CORRECTION),
        event("e2", VoiceEditKind.PARAGRAPH_BREAK, VoiceEditInterpretation.FORMATTING_COMMAND),
        event("e3", VoiceEditKind.INSERT, VoiceEditInterpretation.DOCUMENT_CONTENT),
        event("e4", VoiceEditKind.DELETE_RECENT, VoiceEditInterpretation.UNRESOLVED),
    ]
    summary = derive_correction_metric(
        events,
        SelfObservationPolicy(enabled=True, window_label="session:1"),
    )
    assert summary is not None
    assert summary.event_count == 4
    assert summary.correction_count == 1
    assert summary.formatting_count == 1
    assert summary.content_count == 1
    assert summary.unresolved_count == 1
    assert summary.correction_fraction == 0.25


def test_statibaker_projection_requires_separate_share_opt_in_and_has_no_content():
    correction = event(
        "e1",
        VoiceEditKind.REPLACE_RECENT,
        VoiceEditInterpretation.SELF_CORRECTION,
        "secret-old-text",
        "secret-new-text",
    )
    local_policy = SelfObservationPolicy(enabled=True, share_with_statibaker=False)
    summary = derive_correction_metric([correction], local_policy)
    assert statibaker_metric_signal(summary, local_policy) is None

    shared_policy = SelfObservationPolicy(enabled=True, share_with_statibaker=True)
    shared_summary = derive_correction_metric([correction], shared_policy)
    signal = statibaker_metric_signal(
        shared_summary,
        shared_policy,
        observed_at="2026-09-11T00:00:00Z",
    )
    assert signal is not None
    payload = repr(signal)
    assert "secret-old-text" not in payload
    assert "secret-new-text" not in payload
    assert "span:e1" not in payload
    assert signal["semantics"] == "observational_only_not_diagnostic_or_evaluative"
