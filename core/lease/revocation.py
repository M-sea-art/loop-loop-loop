"""Persistent stop/revoke protocol primitives.

Human stop decisions must become durable runtime facts rather than temporary
signals. Automatic recovery cannot bypass a recorded revoke event.
"""

from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass(frozen=True)
class Revocation:
    goal_id: str
    reason: str
    actor: str = "human"
    created_at: str = ""

    def __post_init__(self):
        if not self.created_at:
            object.__setattr__(
                self,
                "created_at",
                datetime.now(timezone.utc).isoformat(),
            )


class RevocationRegistry:
    def __init__(self):
        self._revoked = {}

    def revoke(self, goal_id: str, reason: str) -> Revocation:
        event = Revocation(goal_id=goal_id, reason=reason)
        self._revoked[goal_id] = event
        return event

    def is_revoked(self, goal_id: str) -> bool:
        return goal_id in self._revoked

    def get(self, goal_id: str):
        return self._revoked.get(goal_id)
