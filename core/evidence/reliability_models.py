"""Evidence models for reality-bound verification.

Evidence should prove an outcome, not merely prove that a file exists.
"""

from dataclasses import dataclass
import hashlib
from pathlib import Path


@dataclass(frozen=True)
class EvidenceRecord:
    event_id: str
    goal_id: str
    outcome_id: str
    scenario_id: str
    artifact_path: str
    evidence_type: str
    direct: bool = True
    verified_by: str = ""
    artifact_hash: str = ""
    contract_hash: str = ""

    def proves_scenario(self, workspace: str | Path | None = None) -> bool:
        if not all(
            (
                self.goal_id,
                self.event_id,
                self.outcome_id,
                self.scenario_id,
                self.artifact_path,
                self.evidence_type,
                self.verified_by,
                self.artifact_hash,
                self.contract_hash,
            )
        ) or not self.direct:
            return False
        if workspace is None:
            return True
        root = Path(workspace).resolve()
        artifact = (root / self.artifact_path).resolve()
        if not artifact.is_relative_to(root) or not artifact.is_file():
            return False
        return hashlib.sha256(artifact.read_bytes()).hexdigest() == self.artifact_hash
