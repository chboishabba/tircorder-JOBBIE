"""Anchor-dependent, namespaced spoken grammar registry.

This layer models extensible command vocabulary as private lexemes rather than
as one global string->action dictionary.  A surface form only acquires command
meaning under an explicit namespace/context and, when required, a shared-anchor
receipt.  Lookup returns candidate branches plus residual alternatives; it does
not execute edits.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Iterable

from .voice_edits import VoiceEditInterpretation, VoiceEditKind


class GrammarNamespace(str, Enum):
    DICTATION = "dictation"
    EDITING = "editing"
    CODING = "coding"
    SHELL = "shell"
    NAVIGATION = "navigation"
    PERSONAL = "personal-custom"


@dataclass(frozen=True)
class SharedAnchorReceipt:
    anchor_id: str
    namespace: GrammarNamespace
    context_reference: str
    active: bool = True


@dataclass(frozen=True)
class PrivateLexemeRule:
    rule_id: str
    surface: str
    intended_meaning: str
    contextual_use: str
    namespace: GrammarNamespace
    output_fibre: VoiceEditInterpretation
    output_kind: VoiceEditKind
    argument: str = ""
    requires_shared_anchor: bool = True
    source_provenance_reference: str = "user-registered"


@dataclass(frozen=True)
class GrammarBranch:
    rule: PrivateLexemeRule
    matched_surface: str
    anchor_satisfied: bool
    context_satisfied: bool
    candidate_score: int
    rationale: str


@dataclass(frozen=True)
class GrammarLookupResult:
    utterance: str
    namespace: GrammarNamespace
    candidates: tuple[GrammarBranch, ...]
    residual_surfaces: tuple[str, ...]

    @property
    def has_residual(self) -> bool:
        return bool(self.residual_surfaces)


def _norm(text: str) -> str:
    return " ".join(text.strip().lower().split())


class GrammarRegistry:
    def __init__(self, rules: Iterable[PrivateLexemeRule] = ()) -> None:
        self._rules = tuple(rules)

    @property
    def rules(self) -> tuple[PrivateLexemeRule, ...]:
        return self._rules

    def register(self, rule: PrivateLexemeRule) -> "GrammarRegistry":
        """Return a new registry; historical registries remain immutable."""
        if any(existing.rule_id == rule.rule_id for existing in self._rules):
            raise ValueError(f"duplicate rule_id: {rule.rule_id}")
        return GrammarRegistry((*self._rules, rule))

    def lookup(
        self,
        utterance: str,
        *,
        namespace: GrammarNamespace,
        context_reference: str = "",
        anchor: SharedAnchorReceipt | None = None,
    ) -> GrammarLookupResult:
        observed = _norm(utterance)
        candidates: list[GrammarBranch] = []
        residual: list[str] = []

        for rule in self._rules:
            if _norm(rule.surface) != observed:
                continue

            namespace_ok = rule.namespace is namespace
            context_ok = namespace_ok and (
                not rule.contextual_use
                or not context_reference
                or rule.contextual_use == context_reference
            )
            anchor_ok = not rule.requires_shared_anchor or (
                anchor is not None
                and anchor.active
                and anchor.namespace is namespace
                and (not context_reference or anchor.context_reference == context_reference)
            )

            score = 100
            if not namespace_ok:
                score -= 50
            if not context_ok:
                score -= 30
            if not anchor_ok:
                score -= 40

            candidates.append(
                GrammarBranch(
                    rule=rule,
                    matched_surface=utterance,
                    anchor_satisfied=anchor_ok,
                    context_satisfied=context_ok,
                    candidate_score=max(score, 0),
                    rationale=(
                        "surface matched private lexeme; namespace/context/anchor "
                        "remain independent admission coordinates"
                    ),
                )
            )

            if not (namespace_ok and context_ok and anchor_ok):
                residual.append(rule.rule_id)

        return GrammarLookupResult(
            utterance=utterance,
            namespace=namespace,
            candidates=tuple(sorted(candidates, key=lambda b: (-b.candidate_score, b.rule.rule_id))),
            residual_surfaces=tuple(sorted(residual)),
        )


BUILTIN_EDITING_GRAMMAR = GrammarRegistry(
    (
        PrivateLexemeRule(
            "builtin:new-paragraph",
            "new paragraph",
            "insert paragraph break",
            "",
            GrammarNamespace.EDITING,
            VoiceEditInterpretation.FORMATTING_COMMAND,
            VoiceEditKind.PARAGRAPH_BREAK,
            requires_shared_anchor=False,
            source_provenance_reference="tircorder.voice_intent.rule-v1",
        ),
        PrivateLexemeRule(
            "builtin:question-mark",
            "question mark",
            "append question mark",
            "",
            GrammarNamespace.EDITING,
            VoiceEditInterpretation.FORMATTING_COMMAND,
            VoiceEditKind.PUNCTUATE,
            argument="?",
            requires_shared_anchor=False,
            source_provenance_reference="tircorder.voice_intent.rule-v1",
        ),
    )
)
