import unittest

from examples.runtime_reliability.e2e_acceptance.run_acceptance import run_acceptance


class EndToEndAcceptanceTests(unittest.TestCase):
    def test_acceptance_runner_executes_all_scenarios(self):
        result = run_acceptance()
        self.assertEqual(result["status"], "VERIFIED_COMPLETE")
        self.assertEqual(
            result["scenarios"],
            {
                "success_case": "VERIFIED_COMPLETE",
                "revoke_case": "VERIFIED_STOPPED",
                "no_progress_case": "STOPPED_NO_PROGRESS",
                "writer_conflict_case": "SECOND_WRITER_REJECTED",
            },
        )


if __name__ == "__main__":
    unittest.main()
