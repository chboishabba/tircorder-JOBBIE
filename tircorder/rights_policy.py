"""Rights-first policy primitives for sensitive TiRCorder actions.

The module deliberately separates observed data, requested actions, purpose,
and authority.  Possessing a recording or health record is never itself an
authority receipt for processing or disclosure.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import FrozenSet, Optional


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
class PolicyRequest:
    subject_id: str
    action: Action
    purpose: str
    data_class: DataClass
    authority: Optional[AuthorityReceipt] = None


@dataclass(frozen=True)
class PolicyDecision:
    allowed: bool
    reason: str


def evaluate(request: PolicyRequest) -> PolicyDecision:
    """Evaluate an action without reconstructing authority from possession.

    Local ingest of general material is allowed without a disclosure receipt.
    Sensitive processing and any outward-facing action require explicit,
    purpose-scoped authority.
    """
    if request.action is Action.INGEST and request.data_class is DataClass.GENERAL:
        return PolicyDecision(True, "local general-data ingest")

    receipt = request.authority
    if receipt is None:
        return PolicyDecision(False, "no authority receipt")
    if receipt.subject_id != request.subject_id:
        return PolicyDecision(False, "authority belongs to another subject")
    if request.action not in receipt.actions:
        return PolicyDecision(False, "action outside authority scope")
    if request.purpose not in receipt.purposes:
        return PolicyDecision(False, "purpose outside authority scope")
    if request.data_class not in receipt.data_classes:
        return PolicyDecision(False, "data class outside authority scope")

    return PolicyDecision(True, f"allowed by {receipt.kind.value}")


def possession_implies_authority(_: DataClass) -> bool:
    """BIDI regression boundary: possession never proves authority."""
    return False


def observation_implies_capacity(_: object) -> bool:
    """BIDI regression boundary: observations never determine legal capacity."""
    return False


def diagnosis_implies_permission(_: object) -> bool:
    """BIDI regression boundary: health/disability labels never grant access."""
    return False
