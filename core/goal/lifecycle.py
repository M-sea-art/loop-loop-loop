"""End-to-end lifecycle for one narrow, verifiable file goal."""

from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import json
from pathlib import Path
import uuid

from core.evidence.collector import EvidenceCollector
from core.evidence.models import EvidenceLedger
from core.executor.executor import ExecutionResult, Executor
from core.goal.goal_contract import GoalContract
from core.judge.policy_gate import GateDecision, PolicyGate
from core.judge.verifier import Judge, VerificationResult
from core.planner.planner import PlanStep, Planner
from core.runtime.artifact_reviewer import ArtifactReviewer
from core.runtime.goal_authority import GoalAuthority
from core.runtime.reliability_runtime import ReliabilityRuntime


@dataclass
class GoalRunResult:
    status: str
    trace: list[str]
    goal: GoalContract
    plan: list[PlanStep] = field(default_factory=list)
    executions: list[ExecutionResult] = field(default_factory=list)
    evidence: EvidenceLedger = field(default_factory=EvidenceLedger)
    review: VerificationResult | None = None
    decision: GateDecision | None = None


def _sections(markdown: str) -> dict[str, list[str]]:
    result: dict[str, list[str]] = {}
    current: str | None = None
    for raw_line in markdown.splitlines():
        line = raw_line.rstrip()
        if line.startswith("## "):
            current = line[3:].strip().lower()
            result[current] = []
        elif current is not None:
            result[current].append(line)
    return result


def _text_section(sections: dict[str, list[str]], name: str) -> str:
    return "\n".join(sections.get(name, [])).strip()


def _list_section(sections: dict[str, list[str]], name: str) -> list[str]:
    return [
        line.lstrip("-* ").strip()
        for line in sections.get(name, [])
        if line.lstrip("-* ").strip()
    ]


class GoalLifecycle:
    def __init__(self, workspace: Path | str):
        self.workspace = Path(workspace).resolve()
        self.planner = Planner()
        self.executor = Executor(self.workspace)
        self.collector = EvidenceCollector(self.workspace)
        self.judge = Judge(self.workspace)
        self.gate = PolicyGate()

    def load_goal(self, goal_file: Path | str) -> GoalContract:
        path = Path(goal_file)
        sections = _sections(path.read_text(encoding="utf-8"))
        goal = GoalContract(
            objective=_text_section(sections, "objective"),
            desired_state=_text_section(sections, "desired state"),
            target_path=_text_section(sections, "target file").strip("`"),
            expected_content=_text_section(sections, "required content"),
            acceptance_criteria=_list_section(sections, "acceptance criteria"),
            constraints=_list_section(sections, "constraints"),
        )
        if not goal.is_well_defined():
            raise ValueError(f"incomplete goal contract: {path}")
        return goal

    def run(self, goal_file: Path | str) -> GoalRunResult:
        trace: list[str] = []
        goal = self.load_goal(goal_file)
        trace.append("GOAL_LOADED")
        plan = self.planner.create_plan(goal)
        trace.append("PLAN_CREATED")

        contract_payload = {
            "objective": goal.objective,
            "desired_state": goal.desired_state,
            "target_path": goal.target_path,
            "expected_content": goal.expected_content,
            "acceptance_criteria": goal.acceptance_criteria,
            "constraints": goal.constraints,
        }
        contract_hash = hashlib.sha256(
            json.dumps(contract_payload, sort_keys=True).encode("utf-8")
        ).hexdigest()
        goal_id = f"goal-{contract_hash[:12]}-{uuid.uuid4().hex[:8]}"
        reviewer_capability = GoalAuthority(self.workspace).freeze(
            goal_id=goal_id,
            contract_hash=contract_hash,
            outcome_id=f"outcome-{contract_hash[:16]}",
            scenario_id=f"scenario-{contract_hash[:16]}",
            artifact_path=goal.target_path,
            expected_content=goal.expected_content,
        )
        reliability = ReliabilityRuntime(self.workspace)
        lease = reliability.acquire_writer(
            project_id="loop-loop-loop",
            goal_id=goal_id,
            writer="runtime-worker",
            thread_id="goal-lifecycle",
            contract_hash=contract_hash,
        )
        executions: list[ExecutionResult] = []
        authority_events = []
        for step in plan:
            if step.action != "write_file":
                executions.append(ExecutionResult(step.action, "REJECTED"))
                continue
            event = reliability.commit_artifact(
                goal_id=lease.goal_id,
                writer=lease.writer,
                contract_hash=lease.contract_hash,
                artifact_path=step.target_path,
                content=step.content,
            )
            authority_events.append(event)
            executions.append(
                ExecutionResult(
                    step.action,
                    "EXECUTED",
                    {"artifact": step.target_path, "event_id": event.event_id},
                )
            )
        trace.append("ACTIONS_EXECUTED")
        if not executions or any(result.status != "EXECUTED" for result in executions):
            return GoalRunResult("EXECUTION_FAILED", trace, goal, plan, executions)

        evidence = self.collector.collect(goal)
        trace.append("EVIDENCE_RECORDED")
        review = self.judge.verify(goal, evidence)
        decision = self.gate.evaluate(goal, evidence, review)
        if decision.status == "VERIFIED_COMPLETE" and authority_events:
            reliable_review = ArtifactReviewer(
                self.workspace, reviewer_capability
            ).verify_artifact(authority_events[-1].event_id)
            if not reliable_review.decision.passed:
                review = VerificationResult(False, [reliable_review.decision.reason])
                decision = GateDecision(
                    reliable_review.status, [reliable_review.decision.reason]
                )
        trace.append("INDEPENDENTLY_VERIFIED" if review.passed else "VERIFICATION_FAILED")
        trace.append(decision.status)
        return GoalRunResult(
            decision.status,
            trace,
            goal,
            plan,
            executions,
            evidence,
            review,
            decision,
        )
