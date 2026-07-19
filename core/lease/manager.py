"""Lease lifecycle management for runtime reliability.

A lease represents temporary authority to mutate a goal execution state.
The manager intentionally keeps authorization narrow: no lease means no write.
"""

from dataclasses import replace
from datetime import datetime, timezone
import json
from pathlib import Path
from threading import Lock

from .models import WriterLease
from .validation import READ_ONLY_ACTORS
from core.storage_lock import exclusive_file_lock


class LeaseManager:
    def __init__(self, path: str | Path | None = None):
        self.path = Path(path) if path else None
        self._lock = Lock()
        self._leases = {}
        self._load()

    def _load(self) -> None:
        if not self.path or not self.path.exists():
            return
        payload = json.loads(self.path.read_text(encoding="utf-8"))
        self._leases = {
            goal_id: WriterLease(**item) for goal_id, item in payload.items()
        }

    def _save(self) -> None:
        if not self.path:
            return
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix(self.path.suffix + ".tmp")
        temporary.write_text(
            json.dumps(
                {key: lease.to_dict() for key, lease in self._leases.items()},
                sort_keys=True,
            ),
            encoding="utf-8",
        )
        temporary.replace(self.path)

    def acquire(self, lease: WriterLease) -> WriterLease:
        with self._lock:
            with exclusive_file_lock(self.path):
                self._load()
                if lease.writer in READ_ONLY_ACTORS:
                    raise PermissionError(f"{lease.writer} is read-only")
                existing = self._leases.get(lease.goal_id)
                if existing and not self.is_expired(existing):
                    raise RuntimeError("active writer lease already exists")
                if self.is_expired(lease):
                    raise ValueError("cannot acquire an expired writer lease")
                self._leases[lease.goal_id] = lease
                self._save()
        return lease

    def get(self, goal_id: str):
        self._load()
        return self._leases.get(goal_id)

    def renew(self, goal_id: str, expires_at: str) -> WriterLease:
        with self._lock, exclusive_file_lock(self.path):
            self._load()
            lease = self._leases[goal_id]
            if self.is_expired(lease):
                raise RuntimeError("expired writer lease cannot be renewed")
            renewed = replace(lease, expires_at=expires_at)
            if self.is_expired(renewed):
                raise ValueError("renewal must extend into the future")
            self._leases[goal_id] = renewed
            self._save()
        return renewed

    def revoke(self, goal_id: str):
        with self._lock, exclusive_file_lock(self.path):
            self._load()
            lease = self._leases.pop(goal_id, None)
            self._save()
        return lease

    def has_writer(self, goal_id: str, writer: str) -> bool:
        self._load()
        lease = self._leases.get(goal_id)
        return bool(
            lease
            and not self.is_expired(lease)
            and lease.is_owned_by(writer)
        )

    def is_expired(self, lease: WriterLease) -> bool:
        now = datetime.now(timezone.utc)
        expiry = datetime.fromisoformat(lease.expires_at)
        if expiry.tzinfo is None:
            raise ValueError("lease expiry must include a timezone")
        return expiry <= now
