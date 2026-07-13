"""Collect direct file evidence without deciding whether the goal passed."""

from __future__ import annotations

import hashlib
from pathlib import Path

from core.evidence.models import EvidenceLedger, EvidenceRecord
from core.goal.goal_contract import GoalContract


class EvidenceCollector:
    def __init__(self, workspace: Path | str):
        self.workspace = Path(workspace).resolve()

    def _artifact_path(self, relative_path: str) -> Path:
        artifact = (self.workspace / relative_path).resolve()
        if not artifact.is_relative_to(self.workspace):
            raise ValueError("evidence artifact must stay inside the workspace")
        return artifact

    def collect(self, goal: GoalContract) -> EvidenceLedger:
        """Read the artifact directly and bind it to every acceptance claim."""

        artifact = self._artifact_path(goal.target_path)
        exists = artifact.is_file()
        payload = artifact.read_bytes() if exists else None
        observed = payload.decode("utf-8") if payload is not None else None
        digest = hashlib.sha256(payload).hexdigest() if payload is not None else None
        ledger = EvidenceLedger()

        for claim in goal.acceptance_criteria:
            ledger.add(
                EvidenceRecord(
                    claim_id=claim,
                    artifact=goal.target_path,
                    expected_content=goal.expected_content,
                    observed_content=observed,
                    artifact_sha256=digest,
                    exists=exists,
                )
            )
        return ledger
