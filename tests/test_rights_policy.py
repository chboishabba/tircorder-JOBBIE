from tircorder.rights_policy import (
    Action,
    AuthorityKind,
    AuthorityReceipt,
    DataClass,
    PolicyRequest,
    diagnosis_implies_permission,
    evaluate,
    observation_implies_capacity,
    possession_implies_authority,
)


def _receipt(**overrides):
    values = {
        "kind": AuthorityKind.SUBJECT_CONSENT,
        "subject_id": "person-1",
        "purposes": frozenset({"care"}),
        "actions": frozenset({Action.PROCESS, Action.SHARE}),
        "data_classes": frozenset({DataClass.HEALTH}),
    }
    values.update(overrides)
    return AuthorityReceipt(**values)


def test_sensitive_processing_requires_authority_receipt():
    decision = evaluate(
        PolicyRequest("person-1", Action.PROCESS, "care", DataClass.HEALTH)
    )
    assert not decision.allowed
    assert decision.reason == "no authority receipt"


def test_authority_is_purpose_action_and_data_scoped():
    receipt = _receipt()
    assert evaluate(
        PolicyRequest("person-1", Action.PROCESS, "care", DataClass.HEALTH, receipt)
    ).allowed
    assert not evaluate(
        PolicyRequest("person-1", Action.EXPORT, "care", DataClass.HEALTH, receipt)
    ).allowed
    assert not evaluate(
        PolicyRequest("person-1", Action.PROCESS, "research", DataClass.HEALTH, receipt)
    ).allowed
    assert not evaluate(
        PolicyRequest("person-1", Action.PROCESS, "care", DataClass.LOCATION, receipt)
    ).allowed


def test_authority_cannot_cross_subjects():
    decision = evaluate(
        PolicyRequest(
            "person-2", Action.PROCESS, "care", DataClass.HEALTH, _receipt()
        )
    )
    assert not decision.allowed
    assert decision.reason == "authority belongs to another subject"


def test_bidi_non_collapse_boundaries():
    assert possession_implies_authority(DataClass.HEALTH) is False
    assert observation_implies_capacity({"speech": "confused"}) is False
    assert diagnosis_implies_permission("any-label") is False
