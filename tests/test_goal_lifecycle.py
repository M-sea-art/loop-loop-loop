from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from core.evidence.collector import EvidenceCollector
from core.executor.executor import Executor
from core.goal.lifecycle import GoalLifecycle
from core.judge.policy_gate import PolicyGate
from core.judge.verifier import Judge, VerificationResult
from core.planner.planner import PlanStep


ROOT = Path(__file__).resolve().parents[1]
EXAMPLE_GOAL = ROOT / "examples" / "simple_goal" / "GOAL.md"


class GoalLifecycleTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.workspace = Path(self.temp.name)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_file_goal_reaches_verified_complete(self) -> None:
        result = GoalLifecycle(self.workspace).run(EXAMPLE_GOAL)

        self.assertEqual(result.status, "VERIFIED_COMPLETE")
        self.assertEqual(
            result.trace,
            [
                "GOAL_LOADED",
                "PLAN_CREATED",
                "ACTIONS_EXECUTED",
                "EVIDENCE_RECORDED",
                "INDEPENDENTLY_VERIFIED",
                "VERIFIED_COMPLETE",
            ],
        )
        self.assertEqual(
            (self.workspace / "result.txt").read_text(encoding="utf-8"),
            "LoopLoopLoop verified this file.",
        )
        self.assertEqual(len(result.plan), 1)
        self.assertEqual(result.plan[0].action, "write_file")
        self.assertEqual(result.plan[0].target_path, "result.txt")
        self.assertTrue(result.evidence.all_verified())
        events = (self.workspace / ".loop/reliability/authority.jsonl").read_text(
            encoding="utf-8"
        )
        self.assertIn("WRITER_LEASE_ACQUIRED", events)
        self.assertIn("ARTIFACT_CHANGED", events)
        self.assertIn("VERIFIED_COMPLETE", events)
        self.assertNotIn("runtime-worker", (self.workspace / ".loop/reliability/leases.json").read_text(encoding="utf-8"))

    def test_independent_judge_rejects_artifact_changed_after_collection(self) -> None:
        lifecycle = GoalLifecycle(self.workspace)
        goal = lifecycle.load_goal(EXAMPLE_GOAL)
        for step in lifecycle.planner.create_plan(goal):
            lifecycle.executor.execute(step)
        evidence = EvidenceCollector(self.workspace).collect(goal)
        (self.workspace / "result.txt").write_text("tampered", encoding="utf-8")

        review = Judge(self.workspace).verify(goal, evidence)

        self.assertFalse(review.passed)
        self.assertTrue(any("changed after collection" in reason for reason in review.reasons))
        self.assertFalse(PolicyGate().evaluate(goal, evidence, review).status == "VERIFIED_COMPLETE")

    def test_policy_gate_rejects_unverified_evidence(self) -> None:
        lifecycle = GoalLifecycle(self.workspace)
        goal = lifecycle.load_goal(EXAMPLE_GOAL)
        for step in lifecycle.planner.create_plan(goal):
            lifecycle.executor.execute(step)
        evidence = lifecycle.collector.collect(goal)

        decision = PolicyGate().evaluate(goal, evidence, VerificationResult(False, ["not reviewed"]))

        self.assertEqual(decision.status, "VERIFICATION_FAILED")
        self.assertIn("evidence is not independently verified", decision.reasons)

    def test_executor_rejects_path_outside_workspace(self) -> None:
        executor = Executor(self.workspace)

        with self.assertRaisesRegex(ValueError, "inside the workspace"):
            executor.execute(PlanStep("write_file", "../escaped.txt", "unsafe"))


if __name__ == "__main__":
    unittest.main()
