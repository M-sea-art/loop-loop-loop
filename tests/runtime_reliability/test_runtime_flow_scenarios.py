from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from examples.runtime_reliability.e2e_acceptance.runtime_flow import run_flow


class RuntimeFlowScenarioTests(unittest.TestCase):
    def test_runtime_flow_executes_reliability_boundaries(self):
        with TemporaryDirectory() as directory:
            result = run_flow("goal-001", directory)
            self.assertEqual(result["status"], "VERIFIED_COMPLETE")
            self.assertTrue(result["evidence_verified"])
            self.assertEqual(
                result["flow"],
                [
                    "frozen_goal_contract",
                    "writer_lease",
                    "mutation_guard",
                    "signed_authority_event",
                    "independent_evidence",
                    "gate",
                ],
            )
            self.assertTrue(Path(directory, "result.txt").is_file())
            self.assertTrue(
                Path(directory, ".loop/reliability/authority.jsonl").is_file()
            )


if __name__ == "__main__":
    unittest.main()
