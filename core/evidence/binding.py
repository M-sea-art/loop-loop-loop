"""Bind evidence to outcomes and verification scenarios.

Evidence should prove a goal-related result, not merely show that an artifact exists.
"""

from dataclasses import dataclass, asdict
from datetime import datetime, timezone
import json


@dataclass(frozen=True)
class EvidenceBinding:
    goal_id: str
    outcome_id: str
    scenario_id: str
    artifact_path: str
    evidence_type: str
    producer: str
    verified_by: str = ""
    artifact_hash: str = ""
    created_at: str = ""

    def to_json(self) -> str:
        data = asdict(self)
        if not data["created_at"]:
            data["created_at"] = datetime.now(timezone.utc).isoformat()
        return json.dumps(data, sort_keys=True)
