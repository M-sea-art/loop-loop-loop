"""Runtime adapter connecting evidence records with execution flow."""

from dataclasses import dataclass


@dataclass(frozen=True)
class VerificationInput:
    goal_id: str
    outcome_id: str
    scenario_id: str
    artifact_path: str


class EvidenceRuntimeAdapter:
    def __init__(self, collector):
        self.collector = collector

    def verify_result(self, event_id: str, item: VerificationInput):
        return self.collector.collect(
            goal_id=item.goal_id,
            event_id=event_id,
            outcome_id=item.outcome_id,
            scenario_id=item.scenario_id,
            artifact_path=item.artifact_path,
            evidence_type="runtime_observation",
        )
