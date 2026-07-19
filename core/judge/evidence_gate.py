"""Evidence driven completion decision boundary."""

from dataclasses import dataclass


@dataclass(frozen=True)
class JudgeDecision:
    passed: bool
    reason: str


class EvidenceGate:
    def __init__(self, workspace=None):
        self.workspace = workspace

    def evaluate(
        self,
        evidence_records: list,
        *,
        goal_id: str = "",
        contract_hash: str = "",
        required_scenarios: set[str] | None = None,
    ) -> JudgeDecision:
        if not evidence_records:
            return JudgeDecision(False, "no evidence available")

        if any(
            not record.proves_scenario(self.workspace)
            for record in evidence_records
        ):
            return JudgeDecision(False, "evidence is incomplete or changed")
        if goal_id and any(record.goal_id != goal_id for record in evidence_records):
            return JudgeDecision(False, "evidence goal mismatch")
        if contract_hash and any(
            record.contract_hash != contract_hash for record in evidence_records
        ):
            return JudgeDecision(False, "evidence contract mismatch")
        covered = {record.scenario_id for record in evidence_records}
        if required_scenarios is not None and covered != required_scenarios:
            return JudgeDecision(False, "required scenario coverage mismatch")

        return JudgeDecision(True, "evidence verified")
