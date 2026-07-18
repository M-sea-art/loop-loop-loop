"""Lease lifecycle management for runtime reliability.

A lease represents temporary authority to mutate a goal execution state.
The manager intentionally keeps authorization narrow: no lease means no write.
"""

from dataclasses import replace
from datetime import datetime, timezone

from .models import WriterLease


class LeaseManager:
    def __init__(self):
        self._leases = {}

    def acquire(self, lease: WriterLease) -> WriterLease:
        existing = self._leases.get(lease.goal_id)
        if existing and not self.is_expired(existing):
            raise RuntimeError("active writer lease already exists")
        self._leases[lease.goal_id] = lease
        return lease

    def get(self, goal_id: str):
        return self._leases.get(goal_id)

    def renew(self, goal_id: str, expires_at: str) -> WriterLease:
        lease = self._leases[goal_id]
        renewed = replace(lease, expires_at=expires_at)
        self._leases[goal_id] = renewed
        return renewed

    def revoke(self, goal_id: str):
        return self._leases.pop(goal_id, None)

    def is_expired(self, lease: WriterLease) -> bool:
        now = datetime.now(timezone.utc)
        expiry = datetime.fromisoformat(lease.expires_at)
        return expiry <= now
