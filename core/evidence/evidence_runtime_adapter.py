"""Runtime adapter connecting evidence records with execution flow."""

from dataclasses import dataclass
import hashlib
from pathlib import Path

from .reliability_models import EvidenceRecord


@dataclass(frozen=True)
class VerificationInput:
    goal_id: str
    outcome_id: str
    scenario_id: str
    artifact_path: str
    contract_hash: str
    expected_content: str


class EvidenceRuntimeAdapter:
    def __init__(self, workspace: str | Path):
        self.workspace = Path(workspace).resolve()

    def verify_result(
        self, event_id: str, item: VerificationInput, verified_by: str
    ) -> EvidenceRecord:
        artifact = (self.workspace / item.artifact_path).resolve()
        if not artifact.is_relative_to(self.workspace):
            raise ValueError("evidence artifact must stay inside the workspace")
        if not artifact.is_file():
            raise FileNotFoundError(item.artifact_path)
        payload = artifact.read_bytes()
        if payload.decode("utf-8") != item.expected_content:
            verified_by = ""
        return EvidenceRecord(
            event_id=event_id,
            goal_id=item.goal_id,
            outcome_id=item.outcome_id,
            scenario_id=item.scenario_id,
            artifact_path=item.artifact_path,
            evidence_type="runtime_observation",
            verified_by=verified_by,
            artifact_hash=hashlib.sha256(payload).hexdigest(),
            contract_hash=item.contract_hash,
        )
