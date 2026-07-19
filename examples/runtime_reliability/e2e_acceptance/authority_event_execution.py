"""Execute one real mutation and recover its signed authority event."""

from pathlib import Path

from core.runtime.goal_authority import GoalAuthority
from core.runtime.reliability_runtime import ReliabilityRuntime


def execute_goal_event(goal_id: str, workspace: str | Path) -> dict:
    contract_hash = f"contract-{goal_id}"
    artifact_path = "authority-event.txt"
    expected_content = "authority event recorded"
    GoalAuthority(workspace).freeze(
        goal_id=goal_id,
        contract_hash=contract_hash,
        outcome_id=f"outcome-{goal_id}",
        scenario_id=f"scenario-{goal_id}",
        artifact_path=artifact_path,
        expected_content=expected_content,
    )
    runtime = ReliabilityRuntime(workspace)
    lease = runtime.acquire_writer(
        project_id="runtime-reliability-example",
        goal_id=goal_id,
        writer="runtime-worker",
        thread_id="authority-event-example",
        contract_hash=contract_hash,
    )
    event = runtime.commit_artifact(
        goal_id=lease.goal_id,
        writer=lease.writer,
        contract_hash=lease.contract_hash,
        artifact_path=artifact_path,
        content=expected_content,
    )
    recovered = next(
        item
        for item in ReliabilityRuntime(workspace).event_log.read_all()
        if item.event_id == event.event_id
    )
    return {
        "goal_id": recovered.goal_id,
        "event_recorded": recovered.action == "ARTIFACT_CHANGED",
        "authority_source": "event_log",
        "event_id": recovered.event_id,
        "artifact_path": recovered.data["artifact_path"],
        "artifact_hash": recovered.data["artifact_hash"],
    }
