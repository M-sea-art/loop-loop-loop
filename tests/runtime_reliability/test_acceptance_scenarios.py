from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from core.runtime.reliability_runtime import ReliabilityRuntime
from core.state.terminal_states import RuntimeTerminalState
from examples.runtime_reliability.e2e_acceptance.runtime_component_wiring import (
    run_component_wiring,
)
from examples.runtime_reliability.e2e_acceptance.runtime_execution_demo import (
    run_success_case,
)
from examples.runtime_reliability.run_all_scenarios import run
from examples.runtime_reliability.scenarios import (
    run_no_progress_case,
    run_revoke_case,
    run_success_case as run_real_success,
    run_writer_conflict_case,
)


class AcceptanceScenarioTests(unittest.TestCase):
    def test_success_case_uses_real_artifact_event_and_projection(self):
        with TemporaryDirectory() as directory:
            result = run_real_success(directory)
            self.assertEqual(result.status, "VERIFIED_COMPLETE")
            self.assertTrue(Path(directory, "result.txt").is_file())
            event_log = Path(directory, ".loop/reliability/authority.jsonl")
            self.assertGreaterEqual(len(event_log.read_text().splitlines()), 2)
            self.assertTrue(any("artifact_hash=" in item for item in result.evidence))

    def test_revoke_survives_reconstruction_and_blocks_artifact(self):
        with TemporaryDirectory() as directory:
            result = run_revoke_case(directory)
            self.assertEqual(result.status, "VERIFIED_STOPPED")
            self.assertFalse(Path(directory, "forbidden.txt").exists())
            self.assertIn("runtime_reconstructed=true", result.evidence)

    def test_no_progress_and_writer_conflict_reach_expected_outcomes(self):
        with TemporaryDirectory() as directory:
            no_progress = run_no_progress_case(directory)
            self.assertEqual(no_progress.status, "STOPPED_NO_PROGRESS")
            rebuilt = ReliabilityRuntime(directory)
            self.assertTrue(rebuilt.revocations.is_revoked("goal-no-progress"))
            self.assertFalse(
                rebuilt.guard.can_mutate("goal-no-progress", "writer-a").allowed
            )
        with TemporaryDirectory() as directory:
            conflict = run_writer_conflict_case(directory)
            self.assertEqual(conflict.status, "SECOND_WRITER_REJECTED")

    def test_all_scenario_runner_executes_not_just_registers(self):
        results = run()
        self.assertEqual(
            {name: result.status for name, result in results.items()},
            {
                "success_case": "VERIFIED_COMPLETE",
                "revoke_case": "VERIFIED_STOPPED",
                "no_progress_case": "STOPPED_NO_PROGRESS",
                "writer_conflict_case": "SECOND_WRITER_REJECTED",
            },
        )

    def test_demo_and_component_wiring_call_real_runtime(self):
        with TemporaryDirectory() as directory:
            result = run_success_case(directory)
            self.assertEqual(result.status, "VERIFIED_COMPLETE")
            self.assertTrue(Path(directory, ".loop/reliability/authority.jsonl").exists())
        with TemporaryDirectory() as directory:
            wiring = run_component_wiring("demo-goal", directory)
            self.assertEqual(wiring.state, "VERIFIED_COMPLETE")
            self.assertTrue(wiring.evidence_verified)

    def test_production_terminal_states_are_complete(self):
        self.assertEqual(
            {item.value for item in RuntimeTerminalState},
            {
                "VERIFIED_COMPLETE",
                "VERIFIED_STOPPED",
                "WAIT_AUTHORITY",
                "STOPPED_NO_PROGRESS",
                "RECONCILE_REQUIRED",
                "FAILED_TERMINAL",
            },
        )


if __name__ == "__main__":
    unittest.main()
