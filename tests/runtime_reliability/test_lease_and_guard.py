from datetime import datetime, timedelta, timezone
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from core.authority.event_log import AuthorityEventLog
from core.authority.models import AuthorityEvent
from core.lease.manager import LeaseManager
from core.lease.models import WriterLease
from core.lease.revocation import RevocationRegistry
from core.runtime.authority_pipeline import AuthorityPipeline
from core.runtime.execution_guard import ExecutionGuard
from core.runtime.goal_authority import GoalAuthority


def freeze_goal(
    directory, goal_id="goal-1", contract_hash="contract-1", artifact_path="result.txt"
):
    return GoalAuthority(directory).freeze(
        goal_id=goal_id,
        contract_hash=contract_hash,
        outcome_id=f"outcome-{goal_id}",
        scenario_id=f"scenario-{goal_id}",
        artifact_path=artifact_path,
        expected_content="expected",
    )


def lease(goal="goal-1", writer="writer-a", seconds=300):
    now = datetime.now(timezone.utc)
    return WriterLease(
        project_id="project-1",
        goal_id=goal,
        writer=writer,
        thread_id=f"thread-{writer}",
        contract_hash="contract-1",
        acquired_at=now.isoformat(),
        expires_at=(now + timedelta(seconds=seconds)).isoformat(),
    )


class LeaseAndGuardTests(unittest.TestCase):
    def test_only_active_owner_can_mutate(self):
        manager = LeaseManager()
        manager.acquire(lease())
        guard = ExecutionGuard(manager, RevocationRegistry())
        self.assertTrue(guard.can_mutate("goal-1", "writer-a").allowed)
        self.assertEqual(
            guard.can_mutate("goal-1", "writer-b").reason,
            "writer_lease_missing",
        )

    def test_second_writer_and_read_only_writer_are_rejected(self):
        manager = LeaseManager()
        manager.acquire(lease())
        with self.assertRaises(RuntimeError):
            manager.acquire(lease(writer="writer-b"))
        with self.assertRaises(PermissionError):
            LeaseManager().acquire(lease(writer="reviewer"))

    def test_concurrent_writers_produce_exactly_one_owner(self):
        manager = LeaseManager()

        def acquire(writer):
            try:
                manager.acquire(lease(writer=writer))
                return writer
            except RuntimeError:
                return None

        with ThreadPoolExecutor(max_workers=2) as pool:
            winners = list(pool.map(acquire, ("writer-a", "writer-b")))
        winners = [winner for winner in winners if winner]
        self.assertEqual(len(winners), 1)
        self.assertTrue(manager.has_writer("goal-1", winners[0]))

    def test_expired_and_naive_expiry_are_rejected(self):
        with self.assertRaises(ValueError):
            LeaseManager().acquire(lease(seconds=-1))
        item = lease()
        item.expires_at = datetime.now().isoformat()
        with self.assertRaises(ValueError):
            LeaseManager().acquire(item)

    def test_lease_and_revocation_survive_runtime_reconstruction(self):
        with TemporaryDirectory() as directory:
            lease_path = Path(directory) / "leases.json"
            revoke_path = Path(directory) / "revocations.json"
            LeaseManager(lease_path).acquire(lease())
            RevocationRegistry(revoke_path).revoke("goal-1", "human stop")
            rebuilt_manager = LeaseManager(lease_path)
            rebuilt_revocations = RevocationRegistry(revoke_path)
            guard = ExecutionGuard(rebuilt_manager, rebuilt_revocations)
            self.assertTrue(rebuilt_manager.has_writer("goal-1", "writer-a"))
            self.assertEqual(
                guard.can_mutate("goal-1", "writer-a").reason,
                "goal_revoked",
            )

    def test_precreated_runtime_instances_cannot_each_acquire_same_goal(self):
        with TemporaryDirectory() as directory:
            from core.runtime.reliability_runtime import ReliabilityRuntime

            freeze_goal(directory)
            first = ReliabilityRuntime(directory)
            second = ReliabilityRuntime(directory)
            first.acquire_writer(
                project_id="project-1",
                goal_id="goal-1",
                writer="writer-a",
                thread_id="thread-a",
                contract_hash="contract-1",
            )
            with self.assertRaises(RuntimeError):
                second.acquire_writer(
                    project_id="project-1",
                    goal_id="goal-1",
                    writer="writer-b",
                    thread_id="thread-b",
                    contract_hash="contract-1",
                )
            lease_events = [
                event
                for event in first.event_log.read_all()
                if event.action == "WRITER_LEASE_ACQUIRED"
            ]
            self.assertEqual(len(lease_events), 1)

    def test_precreated_writer_observes_external_human_revoke(self):
        with TemporaryDirectory() as directory:
            from core.runtime.reliability_runtime import ReliabilityRuntime

            freeze_goal(directory, artifact_path="forbidden.txt")
            writer_runtime = ReliabilityRuntime(directory)
            authority_runtime = ReliabilityRuntime(directory)
            writer_runtime.acquire_writer(
                project_id="project-1",
                goal_id="goal-1",
                writer="writer-a",
                thread_id="thread-a",
                contract_hash="contract-1",
            )
            authority_runtime.revoke_goal("goal-1", "human stop")
            with self.assertRaises(PermissionError):
                writer_runtime.commit_artifact(
                    goal_id="goal-1",
                    writer="writer-a",
                    contract_hash="contract-1",
                    artifact_path="forbidden.txt",
                    content="forbidden",
                )
            actions = [event.action for event in writer_runtime.event_log.read_all()]
            self.assertNotIn("ARTIFACT_CHANGED", actions)

    def test_denied_pipeline_commit_leaves_event_log_unchanged(self):
        with TemporaryDirectory() as directory:
            log = AuthorityEventLog(Path(directory) / "events.jsonl")
            guard = ExecutionGuard(LeaseManager(), RevocationRegistry())
            pipeline = AuthorityPipeline(guard, log)
            event = AuthorityEvent("event-1", "goal-1", "writer-a", "UPDATED")
            decision = pipeline.authorize_and_commit("goal-1", "writer-a", event)
            self.assertFalse(decision.accepted)
            self.assertEqual(log.read_all(), [])

    def test_lease_acquisition_is_audited_and_rolls_back_on_log_failure(self):
        with TemporaryDirectory() as directory:
            from core.runtime.reliability_runtime import ReliabilityRuntime

            freeze_goal(directory)
            runtime = ReliabilityRuntime(directory)
            runtime.acquire_writer(
                project_id="project-1",
                goal_id="goal-1",
                writer="writer-a",
                thread_id="thread-a",
                contract_hash="contract-1",
            )
            event = runtime.event_log.read_all()[0]
            self.assertEqual(event.action, "WRITER_LEASE_ACQUIRED")
            self.assertEqual(event.data["writer"], "writer-a")

            failed = ReliabilityRuntime(Path(directory) / "second")
            freeze_goal(
                Path(directory) / "second",
                goal_id="goal-2",
                contract_hash="contract-2",
            )

            def fail_append(_event):
                raise OSError("simulated log failure")

            failed._event_log.append = fail_append
            with self.assertRaises(OSError):
                failed.acquire_writer(
                    project_id="project-2",
                    goal_id="goal-2",
                    writer="writer-b",
                    thread_id="thread-b",
                    contract_hash="contract-2",
                )
            self.assertIsNone(failed.leases.get("goal-2"))

    def test_event_actor_must_match_authorized_writer(self):
        with TemporaryDirectory() as directory:
            manager = LeaseManager()
            manager.acquire(lease())
            log = AuthorityEventLog(Path(directory) / "events.jsonl")
            pipeline = AuthorityPipeline(
                ExecutionGuard(manager, RevocationRegistry()), log
            )
            event = AuthorityEvent("event-1", "goal-1", "writer-b", "UPDATED")
            decision = pipeline.authorize_and_commit("goal-1", "writer-a", event)
            self.assertEqual(decision.reason, "event_authority_mismatch")
            self.assertEqual(log.read_all(), [])


if __name__ == "__main__":
    unittest.main()
