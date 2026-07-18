"""Evidence driven completion decision boundary."""

from dataclasses import dataclass


@dataclass(frozen=True)
class JudgeDecision:
    passed: bool
    reason: str


class EvidenceGate:
    def evaluate(self, evidence_records: list) -> JudgeDecision:
        if not evidence_records:
            return JudgeDecision(False, "no evidence available")

        return JudgeDecision(True, "evidence supplied for review")
