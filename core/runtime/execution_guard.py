"""Runtime execution guard.

All mutations should pass through this boundary before changing project state.
"""

from dataclasses import dataclass


@dataclass
class MutationDecision:
    allowed: bool
    reason: str


class ExecutionGuard:
    def __init__(self, lease_manager, revocation_registry):
        self.lease_manager = lease_manager
        self.revocation_registry = revocation_registry

    def can_mutate(self, goal_id: str, writer: str) -> MutationDecision:
        if self.revocation_registry.is_revoked(goal_id):
            return MutationDecision(False, "goal_revoked")

        if not self.lease_manager.has_writer(goal_id, writer):
            return MutationDecision(False, "writer_lease_missing")

        return MutationDecision(True, "mutation_authorized")
