from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from core.loop.runtime import LoopRuntime
from core.orchestration.contracts import AgentResult, TaskContract
from core.routing.complexity import ComplexityAnalyzer
from core.routing.models import (
    AuthorizationSource,
    ComplexityProfile,
    ExecutionAuthorization,
    ExecutionMode,
)
from core.routing.policy import ModePolicy
from experts.registry import ExpertProfile, ExpertRegistry, default_registry


def complex_profile() -> ComplexityProfile:
    return ComplexityProfile(
        affected_files=20,
        affected_modules=4,
        domains=("architecture", "implementation", "visual", "qa"),
        risk_level="high",
        parallel_work_items=5,
        specialist_capabilities=("architecture", "implementation", "testing"),
    )


def architecture_contract() -> TaskContract:
    return TaskContract(
        contract_id="architecture",
        goal="Define the implementation boundary.",
        required_capabilities=("architecture", "code_review"),
        inputs=("GOAL.md", "repository"),
        allowed_actions=("inspect_repository", "write_architecture_document"),
        forbidden_actions=("modify_production_code",),
        expected_outputs=("docs/architecture.md",),
        evidence_requirements=("architecture_document_exists",),
    )


class AdaptiveRoutingTestCase(unittest.TestCase):
    def test_simple_goal_recommends_single(self) -> None:
        assessment = ComplexityAnalyzer().assess(ComplexityProfile())

        self.assertEqual(assessment.recommended_mode, ExecutionMode.SINGLE)
        self.assertEqual(assessment.score, 0)

    def test_complexity_cannot_authorize_a_swarm(self) -> None:
        decision = ModePolicy().route(complex_profile())

        self.assertEqual(decision.recommended_mode, ExecutionMode.SWARM)
        self.assertEqual(decision.authorized_ceiling, ExecutionMode.SINGLE)
        self.assertEqual(decision.selected_mode, ExecutionMode.SINGLE)
        self.assertTrue(decision.needs_additional_authorization)
        self.assertTrue(decision.codex_settings_preserved)

    def test_assisted_authorization_caps_swarm_recommendation(self) -> None:
        authorization = ExecutionAuthorization.user_authorized(ExecutionMode.ASSISTED)

        decision = ModePolicy().route(complex_profile(), authorization)

        self.assertEqual(decision.selected_mode, ExecutionMode.ASSISTED)
        self.assertEqual(
            decision.authorization_source,
            AuthorizationSource.CURRENT_USER_REQUEST,
        )

    def test_swarm_requires_explicit_authorization(self) -> None:
        authorization = ExecutionAuthorization.user_authorized(ExecutionMode.SWARM)

        decision = ModePolicy().route(complex_profile(), authorization)

        self.assertEqual(decision.selected_mode, ExecutionMode.SWARM)

    def test_explicit_requested_mode_is_respected_within_ceiling(self) -> None:
        authorization = ExecutionAuthorization.user_authorized(
            ExecutionMode.SWARM,
            requested_mode=ExecutionMode.ASSISTED,
        )

        decision = ModePolicy().route(ComplexityProfile(), authorization)

        self.assertEqual(decision.recommended_mode, ExecutionMode.SINGLE)
        self.assertEqual(decision.selected_mode, ExecutionMode.ASSISTED)

    def test_force_single_wins(self) -> None:
        authorization = ExecutionAuthorization(
            ceiling=ExecutionMode.SWARM,
            source=AuthorizationSource.CURRENT_USER_REQUEST,
            requested_mode=ExecutionMode.SWARM,
            force_single=True,
        )

        decision = ModePolicy().route(complex_profile(), authorization)

        self.assertEqual(decision.selected_mode, ExecutionMode.SINGLE)

    def test_default_source_cannot_expand_authorization(self) -> None:
        with self.assertRaisesRegex(ValueError, "explicit user authorization"):
            ExecutionAuthorization(ceiling=ExecutionMode.ASSISTED)

    def test_arbitrary_source_cannot_claim_authorization(self) -> None:
        with self.assertRaisesRegex(ValueError, "approved user-owned source"):
            ExecutionAuthorization(
                ceiling=ExecutionMode.SWARM,
                source="model_inference",  # type: ignore[arg-type]
            )

    def test_expert_registry_stores_capabilities_not_agents(self) -> None:
        registry = default_registry()

        matches = registry.match(("architecture", "code_review"))

        self.assertEqual([item.profile_id for item in matches], ["software_architect"])
        self.assertFalse(hasattr(matches[0], "run"))

    def test_registry_rejects_duplicate_profiles(self) -> None:
        profile = ExpertProfile("reviewer", ("code_review",))
        registry = ExpertRegistry((profile,))

        with self.assertRaisesRegex(ValueError, "duplicate expert profile"):
            registry.register(profile)

    def test_contract_rejects_conflicting_authority(self) -> None:
        with self.assertRaisesRegex(ValueError, "both allowed and forbidden"):
            TaskContract(
                contract_id="conflict",
                goal="Do bounded work.",
                required_capabilities=("testing",),
                inputs=("build",),
                allowed_actions=("deploy",),
                forbidden_actions=("deploy",),
                expected_outputs=("report.md",),
                evidence_requirements=("report_exists",),
            )

    def test_completed_result_requires_evidence(self) -> None:
        with self.assertRaisesRegex(ValueError, "outputs and evidence_refs"):
            AgentResult("architecture", "COMPLETED", outputs=("architecture.md",))

    def test_runtime_prepares_native_plan_without_touching_codex_config(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            workspace = Path(temp)
            config = workspace / ".codex" / "config.toml"
            config.parent.mkdir()
            config.write_text('model = "codex-default"\n', encoding="utf-8")
            before = config.read_bytes()

            plan = LoopRuntime(workspace).prepare_execution(
                complex_profile(),
                (architecture_contract(),),
                ExecutionAuthorization.user_authorized(ExecutionMode.SWARM),
            )

            self.assertEqual(plan.dispatch_strategy, "codex_native_swarm")
            self.assertEqual(plan.execution_backend, "codex_native")
            self.assertTrue(plan.preserve_codex_defaults)
            self.assertEqual(plan.tasks[0].expert_profile.profile_id, "software_architect")
            self.assertEqual(config.read_bytes(), before)

    def test_default_runtime_plan_stays_with_current_agent(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            plan = LoopRuntime(temp).prepare_execution(
                complex_profile(),
                (architecture_contract(),),
            )

        self.assertEqual(plan.decision.recommended_mode, ExecutionMode.SWARM)
        self.assertEqual(plan.dispatch_strategy, "current_agent_sequential")


if __name__ == "__main__":
    unittest.main()
