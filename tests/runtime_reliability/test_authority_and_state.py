import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from core.authority.event_log import AuthorityEventLog, CorruptEventLog
from core.authority.models import AuthorityEvent
from core.state.projector import StateProjector
from core.state.reconcile import ReconciliationRequired, require_reconciliation


class AuthorityAndStateTests(unittest.TestCase):
    def test_event_round_trip_projects_terminal_state(self):
        with TemporaryDirectory() as directory:
            log = AuthorityEventLog(Path(directory) / "events.jsonl")
            event = AuthorityEvent(
                event_id="event-1",
                goal_id="goal-1",
                actor="human",
                action="GOAL_STATUS_CHANGED",
                data={"to": "VERIFIED_STOPPED"},
            )
            log.append(event)

            events = log.read_all()
            state = StateProjector().project(events)
            self.assertEqual([item.event_id for item in events], ["event-1"])
            self.assertEqual(state.goal_id, "goal-1")
            self.assertEqual(state.status, "VERIFIED_STOPPED")

    def test_duplicate_event_id_is_rejected_without_appending(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "events.jsonl"
            log = AuthorityEventLog(path)
            event = AuthorityEvent("event-1", "goal-1", "writer", "UPDATED")
            log.append(event)
            before = path.read_bytes()
            with self.assertRaises(ValueError):
                log.append(event)
            self.assertEqual(path.read_bytes(), before)

    def test_corrupt_tail_is_not_silently_accepted(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "events.jsonl"
            path.write_text(
                AuthorityEvent("event-1", "goal-1", "writer", "UPDATED").to_json()
                + "\n{partial",
                encoding="utf-8",
            )
            with self.assertRaises(CorruptEventLog):
                AuthorityEventLog(path).read_all()

    def test_projection_drift_requires_reconciliation(self):
        expected = {"goal_id": "goal-1", "status": "ACTIVE"}
        stale = {"goal_id": "goal-1", "status": "VERIFIED_COMPLETE"}
        with self.assertRaises(ReconciliationRequired):
            require_reconciliation(stale, expected)

    def test_required_event_fields_cannot_be_empty(self):
        with self.assertRaises(ValueError):
            AuthorityEvent("", "goal-1", "writer", "UPDATED")


if __name__ == "__main__":
    unittest.main()
