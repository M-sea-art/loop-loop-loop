"""Independent verifier that re-reads actual artifacts."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from pathlib import Path

from core.evidence.models import EvidenceLedger
from core.goal.goal_contract import GoalContract


@dataclass
class VerificationResult:
    passed: bool
    reasons: list[str] = field(default_factory=list)


class Judge:
    def __init__(self, workspace: Path | str):
        self.workspace = Path(workspace).resolve()

    def _artifact_path(self, relative_path: str) -> Path:
        artifact = (self.workspace / relative_path).resolve()
        if not artifact.is_relative_to(self.workspace):
            raise ValueError("verification artifact must stay inside the workspace")
        return artifact

    def verify(self, goal: GoalContract, evidence: EvidenceLedger) -> VerificationResult:
        if not goal.is_well_defined():
            return VerificationResult(False, ["invalid goal contract"])
        if not evidence.records:
            return VerificationResult(False, ["missing evidence"])

        reasons: list[str] = []
        expected_claims = set(goal.acceptance_criteria)
        if (
            evidence.claim_ids() != expected_claims
            or len(evidence.records) != len(expected_claims)
        ):
            reasons.append("evidence does not cover every acceptance claim")

        for record in evidence.records:
            if record.artifact != goal.target_path:
                reasons.append(f"evidence points to the wrong artifact: {record.artifact}")
                continue
            if record.expected_content != goal.expected_content:
                reasons.append(f"evidence is not bound to the goal content: {record.artifact}")
                continue
            artifact = self._artifact_path(record.artifact)
            if not artifact.is_file():
                reasons.append(f"missing artifact: {record.artifact}")
                continue

            payload = artifact.read_bytes()
            observed = payload.decode("utf-8")
            digest = hashlib.sha256(payload).hexdigest()
            if not record.exists:
                reasons.append(f"evidence did not observe the artifact: {record.artifact}")
            elif record.artifact_sha256 != digest:
                reasons.append(f"artifact changed after collection: {record.artifact}")
            elif record.observed_content != observed:
                reasons.append(f"stale observation: {record.artifact}")
            elif observed != goal.expected_content:
                reasons.append(f"content mismatch: {record.artifact}")
            else:
                record.verified = True

        if reasons:
            return VerificationResult(False, reasons)
        return VerificationResult(True)
