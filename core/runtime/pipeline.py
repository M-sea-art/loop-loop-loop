"""Runtime reliability execution pipeline.

This defines the intended order of operations:

Goal -> Executor -> Guard -> Authority Event -> Evidence -> Judge

The pipeline intentionally keeps execution and verification separate.
"""

from dataclasses import dataclass


@dataclass
class PipelineResult:
    accepted: bool
    reason: str


class ReliabilityPipeline:
    def __init__(self, guard, event_writer=None, evidence_collector=None):
        self.guard = guard
        self.event_writer = event_writer
        self.evidence_collector = evidence_collector

    def authorize_execution(self, context):
        decision = self.guard.can_mutate(
            context.goal_id,
            context.writer_id,
        )
        if not decision.allowed:
            return PipelineResult(False, decision.reason)
        return PipelineResult(True, "execution_authorized")
