"""Authority event models for Runtime Reliability v1.

The event log is intended to become the source of truth for runtime state.
Projection files must never become authoritative state.
"""

from dataclasses import dataclass, asdict, field
from datetime import datetime, timezone
import json


@dataclass(frozen=True)
class AuthorityEvent:
    event_id: str
    goal_id: str
    actor: str
    action: str
    previous_state_hash: str = ""
    contract_hash: str = ""
    timestamp: str = ""
    data: dict = field(default_factory=dict)
    signature: str = ""

    def __post_init__(self) -> None:
        for name in ("event_id", "goal_id", "actor", "action"):
            if not getattr(self, name):
                raise ValueError(f"{name} is required")
        if not isinstance(self.data, dict):
            raise ValueError("data must be an object")

    def to_dict(self) -> dict:
        payload = asdict(self)
        if not payload["timestamp"]:
            payload["timestamp"] = datetime.now(timezone.utc).isoformat()
        return payload

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True)

    @classmethod
    def from_json(cls, value: str) -> "AuthorityEvent":
        payload = json.loads(value)
        if not isinstance(payload, dict):
            raise ValueError("authority event must be a JSON object")
        return cls(**payload)
