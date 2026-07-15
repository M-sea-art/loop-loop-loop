"""Public runtime facade for the goal lifecycle."""

from __future__ import annotations

from pathlib import Path

from core.goal.lifecycle import GoalLifecycle, GoalRunResult
from core.orchestration.contracts import TaskContract
from core.orchestration.orchestrator import AdaptiveOrchestrator, OrchestrationPlan
from core.routing.models import ComplexityProfile, ExecutionAuthorization


class LoopRuntime:
    def __init__(
        self,
        workspace: Path | str,
        *,
        orchestrator: AdaptiveOrchestrator | None = None,
    ):
        self.lifecycle = GoalLifecycle(workspace)
        self.orchestrator = orchestrator or AdaptiveOrchestrator()

    def run_once(self, goal_file: Path | str) -> GoalRunResult:
        return self.lifecycle.run(goal_file)

    def prepare_execution(
        self,
        profile: ComplexityProfile,
        contracts: tuple[TaskContract, ...],
        authorization: ExecutionAuthorization | None = None,
    ) -> OrchestrationPlan:
        """Prepare native Codex work without changing the existing goal loop."""

        return self.orchestrator.prepare(profile, contracts, authorization)
