"""Authority event models for Runtime Reliability v1.

The event log is intended to become the source of truth for runtime state.
Projection files must never become authoritative state.
"""

from dataclasses import dataclass, asdict
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

    def to_json(self) -> str:
        payload = asdict(self)
        if not payload["timestamp"]:
            payload["timestamp"] = datetime.now(timezone.utc).isoformat()
        return json.dumps(payload, sort_keys=True)
