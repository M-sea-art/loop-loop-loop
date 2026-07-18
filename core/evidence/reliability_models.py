"""Evidence models for reality-bound verification.

Evidence should prove an outcome, not merely prove that a file exists.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class EvidenceRecord:
    goal_id: str
    outcome_id: str
    scenario_id: str
    artifact_path: str
    evidence_type: str
    direct: bool = True
    verified_by: str = ""

    def proves_scenario(self) -> bool:
        return bool(self.scenario_id and self.artifact_path)
