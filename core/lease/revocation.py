"""Persistent stop/revoke protocol primitives.

Human stop decisions must become durable runtime facts rather than temporary
signals. Automatic recovery cannot bypass a recorded revoke event.
"""

from dataclasses import dataclass
from dataclasses import asdict
from datetime import datetime, timezone
import json
from pathlib import Path
from threading import Lock

from core.storage_lock import exclusive_file_lock


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
    def __init__(self, path: str | Path | None = None):
        self.path = Path(path) if path else None
        self._lock = Lock()
        self._revoked = {}
        self._load()

    def _load(self) -> None:
        if not self.path or not self.path.exists():
            return
        payload = json.loads(self.path.read_text(encoding="utf-8"))
        self._revoked = {
            goal_id: Revocation(**item) for goal_id, item in payload.items()
        }

    def _save(self) -> None:
        if not self.path:
            return
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix(self.path.suffix + ".tmp")
        temporary.write_text(
            json.dumps(
                {key: asdict(value) for key, value in self._revoked.items()},
                sort_keys=True,
            ),
            encoding="utf-8",
        )
        temporary.replace(self.path)

    def revoke(
        self, goal_id: str, reason: str, actor: str = "human"
    ) -> Revocation:
        with self._lock, exclusive_file_lock(self.path):
            self._load()
            event = Revocation(goal_id=goal_id, reason=reason, actor=actor)
            self._revoked[goal_id] = event
            self._save()
        return event

    def is_revoked(self, goal_id: str) -> bool:
        self._load()
        return goal_id in self._revoked

    def get(self, goal_id: str):
        self._load()
        return self._revoked.get(goal_id)
