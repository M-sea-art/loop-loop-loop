from pathlib import Path
from tempfile import TemporaryDirectory
from threading import Event, Thread
import hashlib
import unittest

from core.authority.event_log import AuthorityEventLog
from core.authority.models import AuthorityEvent
from core.runtime.reliability_runtime import ReliabilityRuntime
from core.runtime.artifact_reviewer import ArtifactReviewer
from core.runtime.goal_authority import GoalAuthority, ReviewerCapability


def frozen_runtime(
    directory: str,
    *,
    goal_id: str = "goal-1",
    contract_hash: str = "contract-1",
    artifact_path: str = "result.txt",
    expected_content: str = "expected",
) -> tuple[ReliabilityRuntime, ReviewerCapability]:
    capability = GoalAuthority(directory).freeze(
        goal_id=goal_id,
        contract_hash=contract_hash,
        outcome_id="outcome-1",
        scenario_id="scenario-1",
        artifact_path=artifact_path,
        expected_content=expected_content,
    )
    return ReliabilityRuntime(directory), capability


class RuntimeBoundaryTests(unittest.TestCase):
    def test_contract_mismatch_and_path_escape_do_not_write(self):
        with TemporaryDirectory() as directory:
            runtime, _ = frozen_runtime(directory)
            runtime.acquire_writer(
                project_id="project-1",
                goal_id="goal-1",
                writer="writer-a",
                thread_id="thread-a",
                contract_hash="contract-1",
            )
            with self.assertRaises(PermissionError):
                runtime.commit_artifact(
                    goal_id="goal-1",
                    writer="writer-a",
                    contract_hash="changed-contract",
                    artifact_path="result.txt",
                    content="forbidden",
                )
            with self.assertRaises(ValueError):
                runtime.commit_artifact(
                    goal_id="goal-1",
                    writer="writer-a",
                    contract_hash="contract-1",
                    artifact_path="../escape.txt",
                    content="forbidden",
                )
            self.assertFalse(Path(directory, "result.txt").exists())

    def test_event_log_failure_rolls_back_artifact_mutation(self):
        with TemporaryDirectory() as directory:
            runtime, _ = frozen_runtime(directory)
            runtime.acquire_writer(
                project_id="project-1",
                goal_id="goal-1",
                writer="writer-a",
                thread_id="thread-a",
                contract_hash="contract-1",
            )
            artifact = Path(directory, "result.txt")
            artifact.write_text("before", encoding="utf-8")

            def fail_append(_event):
                raise OSError("simulated event log failure")

            runtime._event_log.append = fail_append
            with self.assertRaises(OSError):
                runtime.commit_artifact(
                    goal_id="goal-1",
                    writer="writer-a",
                    contract_hash="contract-1",
                    artifact_path="result.txt",
                    content="after",
                )
            self.assertEqual(artifact.read_text(encoding="utf-8"), "before")

    def test_projection_rebuilds_from_events_after_projection_loss(self):
        with TemporaryDirectory() as directory:
            runtime, capability = frozen_runtime(directory)
            runtime.acquire_writer(
                project_id="project-1",
                goal_id="goal-1",
                writer="writer-a",
                thread_id="thread-a",
                contract_hash="contract-1",
            )
            event = runtime.commit_artifact(
                goal_id="goal-1",
                writer="writer-a",
                contract_hash="contract-1",
                artifact_path="result.txt",
                content="expected",
            )
            ArtifactReviewer(directory, capability).verify_artifact(event.event_id)
            rebuilt = ReliabilityRuntime(directory)
            state = rebuilt.project_state()
            self.assertEqual(state.goal_id, "goal-1")
            self.assertEqual(state.status, "VERIFIED_COMPLETE")

            Path(directory, "result.txt").write_text("tampered", encoding="utf-8")
            drifted = ReliabilityRuntime(directory).project_state()
            self.assertEqual(drifted.status, "RECONCILE_REQUIRED")

    def test_revoked_goal_cannot_complete_from_old_artifact(self):
        with TemporaryDirectory() as directory:
            runtime, capability = frozen_runtime(directory)
            runtime.acquire_writer(
                project_id="project-1",
                goal_id="goal-1",
                writer="writer-a",
                thread_id="thread-a",
                contract_hash="contract-1",
            )
            event = runtime.commit_artifact(
                goal_id="goal-1",
                writer="writer-a",
                contract_hash="contract-1",
                artifact_path="result.txt",
                content="expected",
            )
            runtime.revoke_goal("goal-1", "human stop")
            result = ArtifactReviewer(directory, capability).verify_artifact(event.event_id)
            self.assertEqual(result.status, "VERIFIED_STOPPED")
            self.assertFalse(result.decision.passed)

    def test_writer_cannot_verify_own_artifact(self):
        with TemporaryDirectory() as directory:
            runtime, _ = frozen_runtime(directory)
            runtime.acquire_writer(
                project_id="project-1",
                goal_id="goal-1",
                writer="writer-a",
                thread_id="thread-a",
                contract_hash="contract-1",
            )
            event = runtime.commit_artifact(
                goal_id="goal-1",
                writer="writer-a",
                contract_hash="contract-1",
                artifact_path="result.txt",
                content="expected",
            )
            from core.runtime.goal_authority import ReviewerCapability

            result = runtime._verify_artifact(
                event.event_id,
                ReviewerCapability("goal-1", "writer-a", "forged"),
            )
            self.assertEqual(result.status, "VERIFICATION_FAILED")
            self.assertFalse(result.decision.passed)

    def test_alias_reviewer_and_fabricated_event_cannot_complete(self):
        with TemporaryDirectory() as directory:
            runtime, capability = frozen_runtime(directory)
            runtime.acquire_writer(
                project_id="project-1",
                goal_id="goal-1",
                writer="writer-a",
                thread_id="thread-a",
                contract_hash="contract-1",
            )
            Path(directory, "result.txt").write_text("expected", encoding="utf-8")
            alias = runtime._verify_artifact(
                "fabricated-event",
                ReviewerCapability("goal-1", "writer-a-alias", "forged"),
            )
            self.assertEqual(alias.status, "VERIFICATION_FAILED")

            fabricated = ArtifactReviewer(directory, capability).verify_artifact(
                "fabricated-event"
            )
            self.assertEqual(fabricated.status, "VERIFICATION_FAILED")
            self.assertIn("authority event", fabricated.decision.reason)

    def test_frozen_contract_rejects_worker_selected_garbage(self):
        with TemporaryDirectory() as directory:
            runtime, capability = frozen_runtime(directory)
            runtime.acquire_writer(
                project_id="project-1",
                goal_id="goal-1",
                writer="writer-a",
                thread_id="thread-a",
                contract_hash="contract-1",
            )
            event = runtime.commit_artifact(
                goal_id="goal-1",
                writer="writer-a",
                contract_hash="contract-1",
                artifact_path="result.txt",
                content="garbage",
            )
            result = ArtifactReviewer(directory, capability).verify_artifact(
                event.event_id
            )
            self.assertEqual(result.status, "VERIFICATION_FAILED")
            self.assertFalse(result.decision.passed)

    def test_raw_event_log_injection_is_not_authentic_evidence(self):
        with TemporaryDirectory() as directory:
            runtime, capability = frozen_runtime(directory)
            runtime.acquire_writer(
                project_id="project-1",
                goal_id="goal-1",
                writer="writer-a",
                thread_id="thread-a",
                contract_hash="contract-1",
            )
            artifact = Path(directory, "result.txt")
            artifact.write_text("expected", encoding="utf-8")
            digest = hashlib.sha256(artifact.read_bytes()).hexdigest()
            AuthorityEventLog(runtime.event_log.path).append(
                AuthorityEvent(
                    "injected",
                    "goal-1",
                    "writer-a",
                    "ARTIFACT_CHANGED",
                    contract_hash="contract-1",
                    data={"artifact_path": "result.txt", "artifact_hash": digest},
                )
            )
            result = ArtifactReviewer(directory, capability).verify_artifact("injected")
            self.assertEqual(result.status, "VERIFICATION_FAILED")
            self.assertIn("authentic", result.decision.reason)
            self.assertFalse(hasattr(runtime.event_log, "append"))

    def test_completion_revokes_lease_and_closes_goal(self):
        with TemporaryDirectory() as directory:
            runtime, capability = frozen_runtime(directory)
            runtime.acquire_writer(
                project_id="project-1",
                goal_id="goal-1",
                writer="writer-a",
                thread_id="thread-a",
                contract_hash="contract-1",
            )
            event = runtime.commit_artifact(
                goal_id="goal-1",
                writer="writer-a",
                contract_hash="contract-1",
                artifact_path="result.txt",
                content="expected",
            )
            self.assertTrue(
                ArtifactReviewer(directory, capability)
                .verify_artifact(event.event_id)
                .decision.passed
            )
            self.assertIsNone(runtime.leases.get("goal-1"))
            with self.assertRaisesRegex(PermissionError, "terminal"):
                runtime.commit_artifact(
                    goal_id="goal-1",
                    writer="writer-a",
                    contract_hash="contract-1",
                    artifact_path="result.txt",
                    content="late mutation",
                )

    def test_multi_goal_projection_stays_goal_scoped(self):
        with TemporaryDirectory() as directory:
            runtime_a, capability_a = frozen_runtime(
                directory, goal_id="goal-a", artifact_path="a.txt"
            )
            runtime_a.acquire_writer(
                project_id="project-1",
                goal_id="goal-a",
                writer="writer-a",
                thread_id="thread-a",
                contract_hash="contract-1",
            )
            event_a = runtime_a.commit_artifact(
                goal_id="goal-a",
                writer="writer-a",
                contract_hash="contract-1",
                artifact_path="a.txt",
                content="expected",
            )
            runtime_a.revoke_goal("goal-a", "stop a")

            runtime_b, capability_b = frozen_runtime(
                directory,
                goal_id="goal-b",
                contract_hash="contract-2",
                artifact_path="b.txt",
            )
            runtime_b.acquire_writer(
                project_id="project-1",
                goal_id="goal-b",
                writer="writer-b",
                thread_id="thread-b",
                contract_hash="contract-2",
            )
            event_b = runtime_b.commit_artifact(
                goal_id="goal-b",
                writer="writer-b",
                contract_hash="contract-2",
                artifact_path="b.txt",
                content="expected",
            )
            self.assertTrue(
                ArtifactReviewer(directory, capability_b)
                .verify_artifact(event_b.event_id)
                .decision.passed
            )
            stopped = ArtifactReviewer(directory, capability_a).verify_artifact(
                event_a.event_id
            )
            self.assertEqual(stopped.status, "VERIFIED_STOPPED")
            self.assertEqual(runtime_b.project_state("goal-a").status, "VERIFIED_STOPPED")
            self.assertEqual(runtime_b.project_state("goal-b").status, "VERIFIED_COMPLETE")

    def test_commit_and_revoke_are_linearized_by_goal_transaction(self):
        with TemporaryDirectory() as directory:
            runtime, _ = frozen_runtime(directory)
            runtime.acquire_writer(
                project_id="project-1",
                goal_id="goal-1",
                writer="writer-a",
                thread_id="thread-a",
                contract_hash="contract-1",
            )
            reached_append = Event()
            release_append = Event()
            original_append = runtime._append_event

            def delayed_append(event):
                if event.action == "ARTIFACT_CHANGED":
                    reached_append.set()
                    release_append.wait(2)
                return original_append(event)

            runtime._append_event = delayed_append
            commit = Thread(
                target=lambda: runtime.commit_artifact(
                    goal_id="goal-1",
                    writer="writer-a",
                    contract_hash="contract-1",
                    artifact_path="result.txt",
                    content="expected",
                )
            )
            revoke = Thread(target=lambda: runtime.revoke_goal("goal-1", "stop"))
            commit.start()
            self.assertTrue(reached_append.wait(2))
            revoke.start()
            self.assertTrue(revoke.is_alive())
            release_append.set()
            commit.join(2)
            revoke.join(2)
            actions = [event.action for event in runtime.event_log.read_all()]
            self.assertEqual(
                actions,
                [
                    "WRITER_LEASE_ACQUIRED",
                    "ARTIFACT_CHANGED",
                    "GOAL_STATUS_CHANGED",
                ],
            )

    def test_stale_store_lock_is_recovered(self):
        with TemporaryDirectory() as directory:
            runtime, _ = frozen_runtime(directory)
            lock = Path(directory, ".loop/reliability/leases.json.lock")
            lock.parent.mkdir(parents=True, exist_ok=True)
            lock.write_text("abandoned", encoding="utf-8")
            runtime.acquire_writer(
                project_id="project-1",
                goal_id="goal-1",
                writer="writer-a",
                thread_id="thread-a",
                contract_hash="contract-1",
            )
            self.assertFalse(lock.exists())

    def test_unchanged_commit_creates_no_event_or_progress(self):
        with TemporaryDirectory() as directory:
            runtime, _ = frozen_runtime(directory)
            runtime.acquire_writer(
                project_id="project-1",
                goal_id="goal-1",
                writer="writer-a",
                thread_id="thread-a",
                contract_hash="contract-1",
            )
            first = runtime.commit_artifact(
                goal_id="goal-1",
                writer="writer-a",
                contract_hash="contract-1",
                artifact_path="result.txt",
                content="expected",
            )
            before = len(runtime.event_log.read_all())
            with self.assertRaisesRegex(ValueError, "unchanged"):
                runtime.commit_artifact(
                    goal_id="goal-1",
                    writer="writer-a",
                    contract_hash="contract-1",
                    artifact_path="result.txt",
                    content="expected",
                )
            self.assertEqual(len(runtime.event_log.read_all()), before)
            runtime.observe_progress(
                "goal-1", {"artifact_changed"}, first.event_id
            )
            runtime.observe_progress(
                "goal-1", {"artifact_changed"}, first.event_id
            )
            self.assertEqual(runtime.progress.cycles("goal-1"), 1)

    def test_completion_review_replay_is_idempotent(self):
        with TemporaryDirectory() as directory:
            runtime, capability = frozen_runtime(directory)
            runtime.acquire_writer(
                project_id="project-1",
                goal_id="goal-1",
                writer="writer-a",
                thread_id="thread-a",
                contract_hash="contract-1",
            )
            event = runtime.commit_artifact(
                goal_id="goal-1",
                writer="writer-a",
                contract_hash="contract-1",
                artifact_path="result.txt",
                content="expected",
            )
            reviewer = ArtifactReviewer(directory, capability)
            first = reviewer.verify_artifact(event.event_id)
            before = len(runtime.event_log.read_all())
            second = reviewer.verify_artifact(event.event_id)
            self.assertTrue(first.decision.passed)
            self.assertTrue(second.decision.passed)
            self.assertEqual(second.decision.reason, "already verified")
            self.assertEqual(len(runtime.event_log.read_all()), before)

    def test_revoke_log_failure_does_not_create_split_authority_state(self):
        with TemporaryDirectory() as directory:
            runtime, _ = frozen_runtime(directory)
            runtime.acquire_writer(
                project_id="project-1",
                goal_id="goal-1",
                writer="writer-a",
                thread_id="thread-a",
                contract_hash="contract-1",
            )
            original_append = runtime._event_log.append

            def fail_append(_event):
                raise OSError("simulated revoke log failure")

            runtime._event_log.append = fail_append
            with self.assertRaises(OSError):
                runtime.revoke_goal("goal-1", "stop")
            self.assertFalse(runtime.revocations.is_revoked("goal-1"))
            self.assertTrue(runtime.leases.has_writer("goal-1", "writer-a"))
            self.assertEqual(runtime.project_state("goal-1").status, "DRAFT")

            runtime._event_log.append = original_append
            runtime.revoke_goal("goal-1", "stop")
            rebuilt = ReliabilityRuntime(directory)
            self.assertTrue(rebuilt.revocations.is_revoked("goal-1"))
            self.assertEqual(
                rebuilt.project_state("goal-1").status, "VERIFIED_STOPPED"
            )


if __name__ == "__main__":
    unittest.main()
