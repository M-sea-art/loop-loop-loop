"""Prepare optional collaboration for execution by the native Codex host."""

from __future__ import annotations

from dataclasses import dataclass

from core.orchestration.contracts import TaskContract
from core.routing.models import (
    ComplexityProfile,
    ExecutionAuthorization,
    ExecutionMode,
    RoutingDecision,
)
from core.routing.policy import ModePolicy
from experts.registry import ExpertProfile, ExpertRegistry, default_registry


@dataclass(frozen=True)
class PreparedTask:
    contract: TaskContract
    expert_profile: ExpertProfile | None


@dataclass(frozen=True)
class OrchestrationPlan:
    decision: RoutingDecision
    tasks: tuple[PreparedTask, ...]
    execution_backend: str = "codex_native"
    preserve_codex_defaults: bool = True

    @property
    def dispatch_strategy(self) -> str:
        return {
            ExecutionMode.SINGLE: "current_agent_sequential",
            ExecutionMode.ASSISTED: "codex_native_assisted",
            ExecutionMode.SWARM: "codex_native_swarm",
        }[self.decision.selected_mode]


class AdaptiveOrchestrator:
    """Route and prepare work; never configure Codex or spawn a custom runtime."""

    def __init__(
        self,
        *,
        mode_policy: ModePolicy | None = None,
        expert_registry: ExpertRegistry | None = None,
    ):
        self.mode_policy = mode_policy or ModePolicy()
        self.expert_registry = expert_registry or default_registry()

    def prepare(
        self,
        profile: ComplexityProfile,
        contracts: tuple[TaskContract, ...],
        authorization: ExecutionAuthorization | None = None,
    ) -> OrchestrationPlan:
        if not contracts:
            raise ValueError("at least one task contract is required")

        decision = self.mode_policy.route(profile, authorization)
        tasks = tuple(
            PreparedTask(
                contract=contract,
                expert_profile=self._match_profile(contract.required_capabilities),
            )
            for contract in contracts
        )
        return OrchestrationPlan(decision=decision, tasks=tasks)

    def _match_profile(self, capabilities: tuple[str, ...]) -> ExpertProfile | None:
        if not capabilities:
            return None
        matches = self.expert_registry.match(capabilities)
        return matches[0] if matches else None
