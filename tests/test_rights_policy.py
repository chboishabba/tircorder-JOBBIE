from tircorder.rights_policy import (
    Action,
    AuthorityKind,
    AuthorityReceipt,
    DataClass,
    GovernanceContext,
    GovernanceCoordinate,
    PermissionReceipt,
    PolicyRequest,
    TranslationEffect,
    content_implies_permission,
    content_implies_provenance,
    diagnosis_implies_permission,
    evaluate,
    extracted_content_translation,
    observation_implies_capacity,
    possession_implies_authority,
    scientific_result_implies_consent,
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


def _cultural_authority():
    return _receipt(
        purposes=frozenset({"research"}),
        actions=frozenset({Action.PROCESS, Action.SHARE}),
        data_classes=frozenset({DataClass.CULTURAL, DataClass.SACRED}),
    )


def _permission(**overrides):
    values = {
        "subject_id": "person-1",
        "purposes": frozenset({"research"}),
        "actions": frozenset({Action.PROCESS}),
        "data_classes": frozenset({DataClass.CULTURAL}),
        "provenance_id": "community-lineage-1",
    }
    values.update(overrides)
    return PermissionReceipt(**values)


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


def test_cultural_authority_does_not_replace_permission():
    decision = evaluate(
        PolicyRequest(
            "person-1",
            Action.PROCESS,
            "research",
            DataClass.CULTURAL,
            _cultural_authority(),
        )
    )
    assert not decision.allowed
    assert decision.reason == "no governance context"


def test_cultural_permission_is_provenance_scoped():
    governance = GovernanceContext(
        provenance_id="community-lineage-2",
        permission=_permission(),
    )
    decision = evaluate(
        PolicyRequest(
            "person-1",
            Action.PROCESS,
            "research",
            DataClass.CULTURAL,
            _cultural_authority(),
            governance,
        )
    )
    assert not decision.allowed
    assert decision.reason == "permission belongs to another provenance"


def test_cultural_obligations_must_be_acknowledged():
    governance = GovernanceContext(
        provenance_id="community-lineage-1",
        permission=_permission(),
        required_obligations=frozenset({"attribution", "benefit-sharing"}),
        acknowledged_obligations=frozenset({"attribution"}),
    )
    decision = evaluate(
        PolicyRequest(
            "person-1",
            Action.PROCESS,
            "research",
            DataClass.CULTURAL,
            _cultural_authority(),
            governance,
        )
    )
    assert not decision.allowed
    assert "benefit-sharing" in decision.reason


def test_cultural_governance_all_coordinates_can_satisfy_gate():
    governance = GovernanceContext(
        provenance_id="community-lineage-1",
        permission=_permission(),
        required_obligations=frozenset({"attribution", "benefit-sharing"}),
        acknowledged_obligations=frozenset({"attribution", "benefit-sharing"}),
    )
    decision = evaluate(
        PolicyRequest(
            "person-1",
            Action.PROCESS,
            "research",
            DataClass.CULTURAL,
            _cultural_authority(),
            governance,
        )
    )
    assert decision.allowed


def test_detached_content_records_governance_erasure():
    receipt = extracted_content_translation()
    assert receipt.effect(GovernanceCoordinate.CONTENT) is TranslationEffect.PRESERVED
    assert receipt.effect(GovernanceCoordinate.PROVENANCE) is TranslationEffect.ERASED
    assert receipt.effect(GovernanceCoordinate.AUTHORITY) is TranslationEffect.ERASED
    assert receipt.effect(GovernanceCoordinate.PERMISSION) is TranslationEffect.ERASED
    assert receipt.effect(GovernanceCoordinate.OBLIGATION) is TranslationEffect.ERASED
    assert not receipt.preserves_governance()


def test_bidi_non_collapse_boundaries():
    assert possession_implies_authority(DataClass.HEALTH) is False
    assert content_implies_provenance("same proposition") is False
    assert content_implies_permission("same proposition") is False
    assert scientific_result_implies_consent("active compound found") is False
    assert observation_implies_capacity({"speech": "confused"}) is False
    assert diagnosis_implies_permission("any-label") is False
