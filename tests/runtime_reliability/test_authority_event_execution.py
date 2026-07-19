from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from examples.runtime_reliability.e2e_acceptance.authority_event_execution import (
    execute_goal_event,
)


class AuthorityEventExecutionTests(unittest.TestCase):
    def test_execution_records_and_recovers_real_event(self):
        with TemporaryDirectory() as directory:
            result = execute_goal_event("goal-demo", directory)
            self.assertTrue(result["event_recorded"])
            self.assertEqual(result["authority_source"], "event_log")
            self.assertTrue(result["event_id"].startswith("evt-"))
            self.assertEqual(result["artifact_path"], "authority-event.txt")
            self.assertTrue(result["artifact_hash"])
            self.assertEqual(
                Path(directory, "authority-event.txt").read_text(encoding="utf-8"),
                "authority event recorded",
            )
            self.assertTrue(
                Path(directory, ".loop/reliability/authority.jsonl").is_file()
            )


if __name__ == "__main__":
    unittest.main()
