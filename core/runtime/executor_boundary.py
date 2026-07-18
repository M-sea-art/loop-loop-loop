"""Reliability boundary for executor mutations.

This module defines the intended integration point between execution and
runtime safety checks. Executors should not directly mutate authoritative state.
"""

from dataclasses import dataclass


@dataclass
class MutationRequest:
    goal_id: str
    writer_id: str
    action: str


class MutationRejected(Exception):
    pass


class ExecutorBoundary:
    def __init__(self, guard):
        self.guard = guard

    def authorize(self, request: MutationRequest) -> bool:
        if not self.guard.allow_mutation(request):
            raise MutationRejected(
                f"mutation rejected for goal={request.goal_id}"
            )
        return True
