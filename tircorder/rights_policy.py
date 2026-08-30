"""Rights-first policy primitives for sensitive TiRCorder actions.

The module deliberately separates observed data, requested actions, purpose,
authority, permission, obligation, and provenance. Possessing a recording,
health record, or cultural knowledge artifact is never itself an authority or
permission receipt for processing or disclosure.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import FrozenSet, Mapping, Optional


class Action(str, Enum):
    INGEST = "ingest"
    PROCESS = "process"
    SHARE = "share"
    EXPORT = "export"
    CONTACT_SERVICE = "contact_service"


class DataClass(str, Enum):
    GENERAL = "general"
    HEALTH = "health"
    DISABILITY = "disability"
    LOCATION = "location"
    CULTURAL = "cultural"
    SACRED = "sacred"
    POLICING = "policing"


class AuthorityKind(str, Enum):
    SUBJECT_CONSENT = "subject_consent"
    STANDING_INSTRUCTION = "standing_instruction"
    REPRESENTATIVE_AUTHORITY = "representative_authority"
    LEGAL_OBLIGATION = "legal_obligation"
    EMERGENCY = "emergency"


class GovernanceCoordinate(str, Enum):
    CONTENT = "content"
    PROVENANCE = "provenance"
    AUTHORITY = "authority"
    PERMISSION = "permission"
    OBLIGATION = "obligation"


class TranslationEffect(str, Enum):
    PRESERVED = "preserved"
    ADDED = "added"
    ERASED = "erased"
    UNRESOLVED = "unresolved"


@dataclass(frozen=True)
class AuthorityReceipt:
    kind: AuthorityKind
    subject_id: str
    purposes: FrozenSet[str]
    actions: FrozenSet[Action]
    data_classes: FrozenSet[DataClass]
    jurisdiction: Optional[str] = None
    expires_at: Optional[str] = None


@dataclass(frozen=True)
class PermissionReceipt:
    """Separate use/disclosure permission for governed material."""

    subject_id: str
    purposes: FrozenSet[str]
    actions: FrozenSet[Action]
    data_classes: FrozenSet[DataClass]
    provenance_id: Optional[str] = None


@dataclass(frozen=True)
class GovernanceContext:
    """Coordinates that must survive independently of the content surface."""

    provenance_id: Optional[str] = None
    permission: Optional[PermissionReceipt] = None
    required_obligations: FrozenSet[str] = frozenset()
    acknowledged_obligations: FrozenSet[str] = frozenset()


@dataclass(frozen=True)
class PolicyRequest:
    subject_id: str
    action: Action
    purpose: str
    data_class: DataClass
    authority: Optional[AuthorityReceipt] = None
    governance: Optional[GovernanceContext] = None


@dataclass(frozen=True)
class PolicyDecision:
    allowed: bool
    reason: str


@dataclass(frozen=True)
class TranslationReceipt:
    """Records what a transformation did to governance coordinates."""

    effects: Mapping[GovernanceCoordinate, TranslationEffect]

    def effect(self, coordinate: GovernanceCoordinate) -> TranslationEffect:
        return self.effects.get(coordinate, TranslationEffect.UNRESOLVED)

    def preserves_governance(self) -> bool:
        return all(
            self.effect(coordinate) is TranslationEffect.PRESERVED
            for coordinate in (
                GovernanceCoordinate.PROVENANCE,
                GovernanceCoordinate.AUTHORITY,
                GovernanceCoordinate.PERMISSION,
                GovernanceCoordinate.OBLIGATION,
            )
        )


def _receipt_covers(request: PolicyRequest, receipt: AuthorityReceipt) -> PolicyDecision:
    if receipt.subject_id != request.subject_id:
        return PolicyDecision(False, "authority belongs to another subject")
    if request.action not in receipt.actions:
        return PolicyDecision(False, "action outside authority scope")
    if request.purpose not in receipt.purposes:
        return PolicyDecision(False, "purpose outside authority scope")
    if request.data_class not in receipt.data_classes:
        return PolicyDecision(False, "data class outside authority scope")
    return PolicyDecision(True, "authority scope satisfied")


def _permission_covers(
    request: PolicyRequest,
    governance: GovernanceContext,
    receipt: PermissionReceipt,
) -> PolicyDecision:
    if receipt.subject_id != request.subject_id:
        return PolicyDecision(False, "permission belongs to another subject")
    if request.action not in receipt.actions:
        return PolicyDecision(False, "action outside permission scope")
    if request.purpose not in receipt.purposes:
        return PolicyDecision(False, "purpose outside permission scope")
    if request.data_class not in receipt.data_classes:
        return PolicyDecision(False, "data class outside permission scope")
    if governance.provenance_id is not None and receipt.provenance_id != governance.provenance_id:
        return PolicyDecision(False, "permission belongs to another provenance")
    return PolicyDecision(True, "permission scope satisfied")


def evaluate(request: PolicyRequest) -> PolicyDecision:
    """Evaluate an action without reconstructing governance from possession.

    Local ingest of general material is allowed without a disclosure receipt.
    Sensitive processing and any outward-facing action require explicit,
    purpose-scoped authority. Cultural and sacred material additionally require
    a separate permission receipt and satisfaction of declared obligations.
    """
    if request.action is Action.INGEST and request.data_class is DataClass.GENERAL:
        return PolicyDecision(True, "local general-data ingest")

    receipt = request.authority
    if receipt is None:
        return PolicyDecision(False, "no authority receipt")

    authority_decision = _receipt_covers(request, receipt)
    if not authority_decision.allowed:
        return authority_decision

    if request.data_class in {DataClass.CULTURAL, DataClass.SACRED}:
        governance = request.governance
        if governance is None:
            return PolicyDecision(False, "no governance context")
        if governance.permission is None:
            return PolicyDecision(False, "no cultural permission receipt")

        permission_decision = _permission_covers(request, governance, governance.permission)
        if not permission_decision.allowed:
            return permission_decision

        missing = governance.required_obligations - governance.acknowledged_obligations
        if missing:
            return PolicyDecision(False, "unacknowledged obligations: " + ", ".join(sorted(missing)))

    return PolicyDecision(True, f"allowed by {receipt.kind.value}")


def extracted_content_translation() -> TranslationReceipt:
    """BIDI calibration: detached content erases governance coordinates."""
    return TranslationReceipt(
        {
            GovernanceCoordinate.CONTENT: TranslationEffect.PRESERVED,
            GovernanceCoordinate.PROVENANCE: TranslationEffect.ERASED,
            GovernanceCoordinate.AUTHORITY: TranslationEffect.ERASED,
            GovernanceCoordinate.PERMISSION: TranslationEffect.ERASED,
            GovernanceCoordinate.OBLIGATION: TranslationEffect.ERASED,
        }
    )


def possession_implies_authority(_: DataClass) -> bool:
    """BIDI regression boundary: possession never proves authority."""
    return False


def content_implies_provenance(_: object) -> bool:
    """BIDI regression boundary: equal content never proves equal provenance."""
    return False


def content_implies_permission(_: object) -> bool:
    """BIDI regression boundary: content never proves permission to use it."""
    return False


def scientific_result_implies_consent(_: object) -> bool:
    """BIDI regression boundary: downstream result never reconstructs consent."""
    return False


def observation_implies_capacity(_: object) -> bool:
    """BIDI regression boundary: observations never determine legal capacity."""
    return False


def diagnosis_implies_permission(_: object) -> bool:
    """BIDI regression boundary: health/disability labels never grant access."""
    return False
