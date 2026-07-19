from pathlib import Path
from tempfile import TemporaryDirectory
from concurrent.futures import ThreadPoolExecutor
import unittest

from core.evidence.evidence_runtime_adapter import (
    EvidenceRuntimeAdapter,
    VerificationInput,
)
from core.judge.evidence_gate import EvidenceGate
from core.progress.detector import NoProgressDetector
from core.progress.invariant import ProgressInvariant, is_real_progress


class ProgressAndEvidenceTests(unittest.TestCase):
    def test_activity_is_not_progress(self):
        self.assertFalse(
            is_real_progress(
                {"heartbeat", "report_created", "state_updated", "agent_spawned"}
            )
        )
        self.assertTrue(is_real_progress({"artifact_changed"}))

    def test_no_progress_isolated_per_goal_and_resets_on_progress(self):
        detector = NoProgressDetector(threshold=2)
        detector.observe(ProgressInvariant({"heartbeat"}), "goal-a")
        detector.observe(ProgressInvariant({"heartbeat"}), "goal-a")
        detector.observe(ProgressInvariant({"heartbeat"}), "goal-b")
        self.assertTrue(detector.should_stop("goal-a"))
        self.assertFalse(detector.should_stop("goal-b"))
        detector.observe(ProgressInvariant({"blocker_removed"}), "goal-a")
        self.assertEqual(detector.cycles("goal-a"), 0)

    def test_invalid_threshold_is_rejected(self):
        with self.assertRaises(ValueError):
            NoProgressDetector(threshold=0)

    def test_no_progress_cycles_survive_reconstruction(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "progress.json"
            first = NoProgressDetector(threshold=3, path=path)
            first.observe(ProgressInvariant({"heartbeat"}), "goal-1")
            second = NoProgressDetector(threshold=3, path=path)
            second.observe(ProgressInvariant({"report_created"}), "goal-1")
            self.assertEqual(second.cycles("goal-1"), 2)

    def test_runtime_reconstruction_does_not_reset_stop_loss(self):
        from core.runtime.reliability_runtime import ReliabilityRuntime

        with TemporaryDirectory() as directory:
            first = ReliabilityRuntime(directory, no_progress_threshold=3)
            self.assertEqual(
                first.observe_progress("goal-1", {"heartbeat"}), "ACTIVE"
            )
            self.assertEqual(
                first.observe_progress("goal-1", {"report_created"}), "ACTIVE"
            )
            rebuilt = ReliabilityRuntime(directory, no_progress_threshold=3)
            self.assertEqual(
                rebuilt.observe_progress("goal-1", {"agent_spawned"}),
                "STOPPED_NO_PROGRESS",
            )
            again = ReliabilityRuntime(directory, no_progress_threshold=3)
            self.assertEqual(
                again.observe_progress("goal-1", {"heartbeat"}),
                "STOPPED_NO_PROGRESS",
            )

    def test_runtime_progress_requires_a_fresh_authentic_event(self):
        from core.runtime.goal_authority import GoalAuthority
        from core.runtime.reliability_runtime import ReliabilityRuntime

        with TemporaryDirectory() as directory:
            GoalAuthority(directory).freeze(
                goal_id="goal-1",
                contract_hash="contract-1",
                outcome_id="outcome-1",
                scenario_id="scenario-1",
                artifact_path="result.txt",
                expected_content="expected",
            )
            runtime = ReliabilityRuntime(directory, no_progress_threshold=3)
            runtime.acquire_writer(
                project_id="project-1",
                goal_id="goal-1",
                writer="writer-a",
                thread_id="thread-a",
                contract_hash="contract-1",
            )
            self.assertEqual(
                runtime.observe_progress("goal-1", {"artifact_changed"}), "ACTIVE"
            )
            event = runtime.commit_artifact(
                goal_id="goal-1",
                writer="writer-a",
                contract_hash="contract-1",
                artifact_path="result.txt",
                content="expected",
            )
            self.assertEqual(
                runtime.observe_progress(
                    "goal-1", {"artifact_changed"}, event.event_id
                ),
                "ACTIVE",
            )
            self.assertEqual(runtime.progress.cycles("goal-1"), 0)
            runtime.observe_progress("goal-1", {"artifact_changed"}, event.event_id)
            runtime.observe_progress("goal-1", {"artifact_changed"}, event.event_id)
            self.assertEqual(runtime.progress.cycles("goal-1"), 2)

    def test_progress_store_updates_are_atomic_across_goals(self):
        from core.runtime.reliability_runtime import ReliabilityRuntime

        with TemporaryDirectory() as directory:
            first = ReliabilityRuntime(directory, no_progress_threshold=1000)
            second = ReliabilityRuntime(directory, no_progress_threshold=1000)

            def observe(runtime, goal_id):
                for _ in range(100):
                    runtime.observe_progress(goal_id, {"heartbeat"})

            with ThreadPoolExecutor(max_workers=2) as pool:
                futures = [
                    pool.submit(observe, first, "goal-a"),
                    pool.submit(observe, second, "goal-b"),
                ]
                for future in futures:
                    future.result()
            rebuilt = ReliabilityRuntime(directory, no_progress_threshold=1000)
            self.assertEqual(rebuilt.progress.cycles("goal-a"), 100)
            self.assertEqual(rebuilt.progress.cycles("goal-b"), 100)

    def test_verified_binding_passes_and_artifact_replacement_fails(self):
        with TemporaryDirectory() as directory:
            artifact = Path(directory) / "result.txt"
            artifact.write_text("expected", encoding="utf-8")
            adapter = EvidenceRuntimeAdapter(directory)
            item = VerificationInput(
                goal_id="goal-1",
                outcome_id="outcome-1",
                scenario_id="scenario-1",
                artifact_path="result.txt",
                contract_hash="contract-1",
                expected_content="expected",
            )
            record = adapter.verify_result("event-1", item, "reviewer-1")
            gate = EvidenceGate(directory)
            self.assertTrue(
                gate.evaluate(
                    [record],
                    goal_id="goal-1",
                    contract_hash="contract-1",
                    required_scenarios={"scenario-1"},
                ).passed
            )
            artifact.write_text("replaced", encoding="utf-8")
            self.assertFalse(gate.evaluate([record]).passed)

    def test_wrong_content_goal_contract_and_coverage_are_rejected(self):
        with TemporaryDirectory() as directory:
            Path(directory, "result.txt").write_text("wrong", encoding="utf-8")
            item = VerificationInput(
                goal_id="goal-1",
                outcome_id="outcome-1",
                scenario_id="scenario-1",
                artifact_path="result.txt",
                contract_hash="contract-1",
                expected_content="expected",
            )
            record = EvidenceRuntimeAdapter(directory).verify_result(
                "event-1", item, "reviewer-1"
            )
            gate = EvidenceGate(directory)
            self.assertFalse(gate.evaluate([record]).passed)
            self.assertFalse(
                gate.evaluate([record], goal_id="other-goal").passed
            )
            self.assertFalse(
                gate.evaluate([record], contract_hash="other-contract").passed
            )
            self.assertFalse(
                gate.evaluate(
                    [record], required_scenarios={"scenario-1", "scenario-2"}
                ).passed
            )


if __name__ == "__main__":
    unittest.main()
