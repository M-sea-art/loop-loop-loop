"""Executable Runtime Reliability v1 acceptance scenarios."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from core.runtime.reliability_runtime import ReliabilityRuntime
from core.runtime.artifact_reviewer import ArtifactReviewer
from core.runtime.goal_authority import GoalAuthority


@dataclass(frozen=True)
class ScenarioResult:
    status: str
    evidence: list[str] = field(default_factory=list)


def run_success_case(workspace: str | Path) -> ScenarioResult:
    reviewer = GoalAuthority(workspace).freeze(
        goal_id="goal-success",
        contract_hash="contract-success",
        outcome_id="outcome-1",
        scenario_id="scenario-1",
        artifact_path="result.txt",
        expected_content="verified result",
    )
    runtime = ReliabilityRuntime(workspace)
    lease = runtime.acquire_writer(
        project_id="demo",
        goal_id="goal-success",
        writer="builder",
        thread_id="thread-1",
        contract_hash="contract-success",
    )
    event = runtime.commit_artifact(
        goal_id=lease.goal_id,
        writer=lease.writer,
        contract_hash=lease.contract_hash,
        artifact_path="result.txt",
        content="verified result",
    )
    result = ArtifactReviewer(workspace, reviewer).verify_artifact(event.event_id)
    state = runtime.project_state(lease.goal_id)
    return ScenarioResult(
        result.status,
        [
            f"artifact_hash={result.artifact_hash}",
            f"last_event_id={state.last_event_id}",
            f"projected_state={state.status}",
        ],
    )


def run_revoke_case(workspace: str | Path) -> ScenarioResult:
    GoalAuthority(workspace).freeze(
        goal_id="goal-revoke",
        contract_hash="contract-revoke",
        outcome_id="outcome-revoke",
        scenario_id="scenario-revoke",
        artifact_path="forbidden.txt",
        expected_content="must not exist",
    )
    runtime = ReliabilityRuntime(workspace)
    lease = runtime.acquire_writer(
        project_id="demo",
        goal_id="goal-revoke",
        writer="builder",
        thread_id="thread-1",
        contract_hash="contract-revoke",
    )
    runtime.revoke_goal(lease.goal_id, "human stop")
    rebuilt = ReliabilityRuntime(workspace)
    before = len(rebuilt.event_log.read_all())
    try:
        rebuilt.commit_artifact(
            goal_id=lease.goal_id,
            writer=lease.writer,
            contract_hash=lease.contract_hash,
            artifact_path="forbidden.txt",
            content="must not exist",
        )
    except PermissionError as exc:
        reason = str(exc)
    else:
        raise AssertionError("revoked goal resumed after runtime reconstruction")
    after = len(rebuilt.event_log.read_all())
    if before != after or (Path(workspace) / "forbidden.txt").exists():
        raise AssertionError("denied mutation changed authoritative state")
    return ScenarioResult(
        rebuilt.project_state(lease.goal_id).status,
        [f"mutation_denied={reason}", "runtime_reconstructed=true"],
    )


def run_no_progress_case(workspace: str | Path) -> ScenarioResult:
    runtime = ReliabilityRuntime(workspace, no_progress_threshold=3)
    statuses = [
        runtime.observe_progress("goal-no-progress", {"heartbeat"}),
        runtime.observe_progress("goal-no-progress", {"report_created"}),
        runtime.observe_progress("goal-no-progress", {"agent_spawned"}),
    ]
    return ScenarioResult(
        statuses[-1],
        [f"cycles={runtime.progress.cycles('goal-no-progress')}", *statuses],
    )


def run_writer_conflict_case(workspace: str | Path) -> ScenarioResult:
    GoalAuthority(workspace).freeze(
        goal_id="goal-conflict",
        contract_hash="contract-conflict",
        outcome_id="outcome-conflict",
        scenario_id="scenario-conflict",
        artifact_path="conflict.txt",
        expected_content="winner",
    )
    runtime = ReliabilityRuntime(workspace)
    runtime.acquire_writer(
        project_id="demo",
        goal_id="goal-conflict",
        writer="writer-a",
        thread_id="thread-a",
        contract_hash="contract-conflict",
    )
    try:
        runtime.acquire_writer(
            project_id="demo",
            goal_id="goal-conflict",
            writer="writer-b",
            thread_id="thread-b",
            contract_hash="contract-conflict",
        )
    except RuntimeError as exc:
        return ScenarioResult(
            "SECOND_WRITER_REJECTED", [f"reason={exc}"]
        )
    raise AssertionError("second writer acquired an active goal lease")
