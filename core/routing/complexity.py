"""Deterministic complexity recommendation for an execution goal."""

from __future__ import annotations

from core.routing.models import ComplexityAssessment, ComplexityProfile, ExecutionMode


class ComplexityAnalyzer:
    """Recommend a mode from explicit goal signals.

    Recommendations are advisory. Authorization is applied separately by
    :class:`ModePolicy`.
    """

    def assess(self, profile: ComplexityProfile) -> ComplexityAssessment:
        score = 0
        reasons: list[str] = []

        if profile.affected_files > 1:
            score += 1
            reasons.append("multiple_files")
        if profile.affected_modules > 1:
            score += 1
            reasons.append("multiple_modules")
        if len(set(profile.domains)) > 1:
            score += 2
            reasons.append("multiple_domains")

        if profile.risk_level == "medium":
            score += 1
            reasons.append("medium_risk")
        elif profile.risk_level == "high":
            score += 2
            reasons.append("high_risk")

        if profile.parallel_work_items >= 4:
            score += 2
            reasons.append("strong_parallel_opportunity")
        elif profile.parallel_work_items >= 2:
            score += 1
            reasons.append("parallel_opportunity")

        if len(set(profile.specialist_capabilities)) > 1:
            score += 1
            reasons.append("multiple_specialist_capabilities")

        if score >= 6:
            mode = ExecutionMode.SWARM
        elif score >= 2:
            mode = ExecutionMode.ASSISTED
        else:
            mode = ExecutionMode.SINGLE

        return ComplexityAssessment(mode, score, tuple(reasons))
