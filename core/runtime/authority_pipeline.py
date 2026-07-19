"""Authority-aware execution pipeline boundary.

The pipeline coordinates safety checks before runtime mutations are committed.
"""

from dataclasses import dataclass


@dataclass
class PipelineResult:
    accepted: bool
    reason: str


class AuthorityPipeline:
    def __init__(self, guard, event_log):
        self.guard = guard
        self.event_log = event_log

    def authorize_and_commit(self, goal_id, writer, event):
        if event.goal_id != goal_id or event.actor != writer:
            return PipelineResult(False, "event_authority_mismatch")
        decision = self.guard.can_mutate(goal_id, writer)
        if not decision.allowed:
            return PipelineResult(False, decision.reason)

        self.event_log.append(event)
        return PipelineResult(True, "committed")
