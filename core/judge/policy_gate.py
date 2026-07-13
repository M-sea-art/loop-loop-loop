"""Deterministic completion gate."""

from __future__ import annotations

from dataclasses import dataclass, field

from core.evidence.models import EvidenceLedger
from core.goal.goal_contract import GoalContract
from core.judge.verifier import VerificationResult


@dataclass(frozen=True)
class GateDecision:
    status: str
    reasons: list[str] = field(default_factory=list)


class PolicyGate:
    def evaluate(
        self,
        goal: GoalContract,
        evidence: EvidenceLedger,
        review: VerificationResult,
    ) -> GateDecision:
        reasons: list[str] = []
        if not goal.is_well_defined():
            reasons.append("invalid goal contract")
        expected_claims = set(goal.acceptance_criteria)
        if (
            evidence.claim_ids() != expected_claims
            or len(evidence.records) != len(expected_claims)
        ):
            reasons.append("acceptance claims are not fully covered")
        if not evidence.all_verified():
            reasons.append("evidence is not independently verified")
        if not review.passed:
            reasons.extend(review.reasons or ["independent verification failed"])

        if reasons:
            return GateDecision("VERIFICATION_FAILED", reasons)
        return GateDecision("VERIFIED_COMPLETE")
