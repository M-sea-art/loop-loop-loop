"""Authorization gate between complexity advice and execution selection."""

from __future__ import annotations

from core.routing.complexity import ComplexityAnalyzer
from core.routing.models import (
    ComplexityAssessment,
    ComplexityProfile,
    ExecutionAuthorization,
    ExecutionMode,
    RoutingDecision,
)


class ModePolicy:
    """Select a mode without exceeding the user-authorized ceiling."""

    def __init__(self, analyzer: ComplexityAnalyzer | None = None):
        self.analyzer = analyzer or ComplexityAnalyzer()

    def route(
        self,
        profile: ComplexityProfile,
        authorization: ExecutionAuthorization | None = None,
    ) -> RoutingDecision:
        return self.select(self.analyzer.assess(profile), authorization)

    def select(
        self,
        assessment: ComplexityAssessment,
        authorization: ExecutionAuthorization | None = None,
    ) -> RoutingDecision:
        permitted = authorization or ExecutionAuthorization()

        if permitted.force_single:
            selected = ExecutionMode.SINGLE
        elif permitted.requested_mode is not None:
            selected = permitted.requested_mode
        else:
            selected = ExecutionMode.lower(
                assessment.recommended_mode,
                permitted.ceiling,
            )

        return RoutingDecision(
            recommended_mode=assessment.recommended_mode,
            authorized_ceiling=permitted.ceiling,
            selected_mode=selected,
            authorization_source=permitted.source,
            reasons=assessment.reasons,
        )
