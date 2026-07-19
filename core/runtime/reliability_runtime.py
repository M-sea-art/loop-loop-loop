"""Runtime Reliability v1 integration boundary used by the production facade."""

from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from datetime import datetime, timedelta, timezone
import hashlib
import hmac
import json
import os
from pathlib import Path
import secrets
import uuid

from core.authority.event_log import AuthorityEventLog
from core.authority.models import AuthorityEvent
from core.evidence.evidence_runtime_adapter import EvidenceRuntimeAdapter, VerificationInput
from core.judge.evidence_gate import EvidenceGate, JudgeDecision
from core.lease.manager import LeaseManager
from core.lease.models import WriterLease
from core.lease.revocation import RevocationRegistry
from core.progress.detector import NoProgressDetector
from core.progress.invariant import ProgressInvariant
from core.runtime.authority_pipeline import AuthorityPipeline
from core.runtime.execution_guard import ExecutionGuard
from core.runtime.goal_authority import GoalContractStore, ReviewerCapability
from core.state.projector import ProjectedState, StateProjector
from core.storage_lock import exclusive_file_lock


@dataclass(frozen=True)
class RuntimeVerification:
    status: str
    decision: JudgeDecision
    artifact_hash: str


class _ReadOnlyAuthorityLog:
    """Public inspection surface without an event injection method."""

    def __init__(self, event_log: AuthorityEventLog):
        self.path = event_log.path
        self._event_log = event_log

    def read_all(self) -> list[AuthorityEvent]:
        return self._event_log.read_all()


class _SignedEventAppender:
    def __init__(self, runtime: "ReliabilityRuntime"):
        self.runtime = runtime

    def append(self, event: AuthorityEvent) -> None:
        self.runtime._append_event(event)


class ReliabilityRuntime:
    def __init__(self, workspace: str | Path, no_progress_threshold: int = 3):
        self.workspace = Path(workspace).resolve()
        self.state_dir = self.workspace / ".loop" / "reliability"
        self._event_log = AuthorityEventLog(self.state_dir / "authority.jsonl")
        self.event_log = _ReadOnlyAuthorityLog(self._event_log)
        self._event_key = self._load_or_create_event_key()
        self.contracts = GoalContractStore(self.state_dir / "contracts.json")
        self.leases = LeaseManager(self.state_dir / "leases.json")
        self.revocations = RevocationRegistry(self.state_dir / "revocations.json")
        self.guard = ExecutionGuard(self.leases, self.revocations)
        self.pipeline = AuthorityPipeline(self.guard, _SignedEventAppender(self))
        self.progress = NoProgressDetector(
            no_progress_threshold, self.state_dir / "progress.json"
        )
        self.evidence = EvidenceRuntimeAdapter(self.workspace)
        self.gate = EvidenceGate(self.workspace)

    def _load_or_create_event_key(self) -> bytes:
        path = self.state_dir / "authority.key"
        with exclusive_file_lock(path):
            if not path.exists():
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(secrets.token_bytes(32))
                os.chmod(path, 0o600)
            key = path.read_bytes()
        if len(key) != 32:
            raise RuntimeError("invalid authority event signing key")
        return key

    def _goal_lock_path(self, goal_id: str) -> Path:
        digest = hashlib.sha256(goal_id.encode("utf-8")).hexdigest()
        return self.state_dir / "goal-transactions" / digest

    @staticmethod
    def _event_payload(event: AuthorityEvent) -> bytes:
        payload = asdict(event)
        payload["signature"] = ""
        return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode(
            "utf-8"
        )

    def _sign_event(self, event: AuthorityEvent) -> AuthorityEvent:
        if not event.timestamp:
            event = replace(event, timestamp=datetime.now(timezone.utc).isoformat())
        signature = hmac.new(
            self._event_key, self._event_payload(event), hashlib.sha256
        ).hexdigest()
        return replace(event, signature=signature)

    def _event_is_authentic(self, event: AuthorityEvent) -> bool:
        if not event.signature:
            return False
        expected = hmac.new(
            self._event_key, self._event_payload(event), hashlib.sha256
        ).hexdigest()
        return hmac.compare_digest(event.signature, expected)

    def _append_event(self, event: AuthorityEvent) -> None:
        self._event_log.append(self._sign_event(event))

    def _active_contract(self, goal_id: str, contract_hash: str):
        contract = self.contracts.get(goal_id)
        if contract is None:
            raise PermissionError("goal contract is not frozen")
        if contract.contract_hash != contract_hash:
            raise PermissionError("contract_hash_mismatch")
        return contract

    def _consume_progress_event(
        self, goal_id: str, event_id: str, artifact_hash: str
    ) -> bool:
        path = self.state_dir / "progress-events.json"
        with exclusive_file_lock(path):
            if path.exists():
                payload = json.loads(path.read_text(encoding="utf-8"))
            else:
                payload = {}
            goal_payload = payload.get(goal_id, {})
            if isinstance(goal_payload, list):
                goal_payload = {"event_ids": goal_payload, "artifact_hashes": []}
            consumed_events = set(goal_payload.get("event_ids", []))
            consumed_hashes = set(goal_payload.get("artifact_hashes", []))
            if event_id in consumed_events or artifact_hash in consumed_hashes:
                return False
            consumed_events.add(event_id)
            consumed_hashes.add(artifact_hash)
            payload[goal_id] = {
                "event_ids": sorted(consumed_events),
                "artifact_hashes": sorted(consumed_hashes),
            }
            path.parent.mkdir(parents=True, exist_ok=True)
            temporary = path.with_suffix(path.suffix + ".tmp")
            temporary.write_text(json.dumps(payload, sort_keys=True), encoding="utf-8")
            temporary.replace(path)
            return True

    def acquire_writer(
        self,
        *,
        project_id: str,
        goal_id: str,
        writer: str,
        thread_id: str,
        contract_hash: str,
        ttl_seconds: int = 300,
    ) -> WriterLease:
        with exclusive_file_lock(self._goal_lock_path(goal_id)):
            self._active_contract(goal_id, contract_hash)
            if self.revocations.is_revoked(goal_id):
                raise PermissionError("goal_revoked")
            state = self.project_state(goal_id)
            if state.status in {"VERIFIED_COMPLETE", "VERIFIED_STOPPED", "STOPPED_NO_PROGRESS"}:
                raise PermissionError("goal_is_terminal")
            now = datetime.now(timezone.utc)
            lease = WriterLease(
                project_id=project_id,
                goal_id=goal_id,
                writer=writer,
                thread_id=thread_id,
                contract_hash=contract_hash,
                acquired_at=now.isoformat(),
                expires_at=(now + timedelta(seconds=ttl_seconds)).isoformat(),
            )
            acquired = self.leases.acquire(lease)
            try:
                self._append_event(
                    AuthorityEvent(
                        event_id=f"evt-{uuid.uuid4().hex}",
                        goal_id=goal_id,
                        actor="runtime-authority",
                        action="WRITER_LEASE_ACQUIRED",
                        contract_hash=contract_hash,
                        data={
                            "writer": writer,
                            "thread_id": thread_id,
                            "expires_at": acquired.expires_at,
                        },
                    )
                )
            except Exception:
                self.leases.revoke(goal_id)
                raise
            return acquired

    def commit_artifact(
        self,
        *,
        goal_id: str,
        writer: str,
        contract_hash: str,
        artifact_path: str,
        content: str,
    ) -> AuthorityEvent:
        with exclusive_file_lock(self._goal_lock_path(goal_id)):
            contract = self._active_contract(goal_id, contract_hash)
            artifact = (self.workspace / artifact_path).resolve()
            if not artifact.is_relative_to(self.workspace):
                raise ValueError("artifact must stay inside the workspace")
            if artifact_path != contract.artifact_path:
                raise PermissionError("artifact_path_not_in_frozen_contract")
            if self.project_state(goal_id).status in {
                "VERIFIED_COMPLETE",
                "VERIFIED_STOPPED",
                "STOPPED_NO_PROGRESS",
            }:
                raise PermissionError("goal_is_terminal")
            decision = self.guard.can_mutate(goal_id, writer)
            if not decision.allowed:
                raise PermissionError(decision.reason)
            lease = self.leases.get(goal_id)
            if lease.contract_hash != contract_hash:
                raise PermissionError("contract_hash_mismatch")
            existed = artifact.is_file()
            previous_payload = artifact.read_bytes() if existed else b""
            next_payload = content.encode("utf-8")
            if existed and previous_payload == next_payload:
                raise ValueError("artifact_unchanged")
            artifact.parent.mkdir(parents=True, exist_ok=True)
            artifact.write_text(content, encoding="utf-8")
            digest = hashlib.sha256(artifact.read_bytes()).hexdigest()
            event = AuthorityEvent(
                event_id=f"evt-{uuid.uuid4().hex}",
                goal_id=goal_id,
                actor=writer,
                action="ARTIFACT_CHANGED",
                contract_hash=contract_hash,
                data={"artifact_path": artifact_path, "artifact_hash": digest},
            )
            try:
                result = self.pipeline.authorize_and_commit(goal_id, writer, event)
            except Exception:
                if existed:
                    artifact.write_bytes(previous_payload)
                else:
                    artifact.unlink(missing_ok=True)
                raise
            if not result.accepted:
                if existed:
                    artifact.write_bytes(previous_payload)
                else:
                    artifact.unlink(missing_ok=True)
                raise PermissionError(result.reason)
            return event

    def revoke_goal(self, goal_id: str, reason: str, actor: str = "human") -> None:
        with exclusive_file_lock(self._goal_lock_path(goal_id)):
            if self.project_state(goal_id).status in {
                "VERIFIED_COMPLETE",
                "VERIFIED_STOPPED",
                "STOPPED_NO_PROGRESS",
            }:
                return
            self._append_event(
                AuthorityEvent(
                    event_id=f"evt-{uuid.uuid4().hex}",
                    goal_id=goal_id,
                    actor=actor,
                    action="GOAL_STATUS_CHANGED",
                    data={"to": "VERIFIED_STOPPED", "reason": reason},
                )
            )
            self.revocations.revoke(goal_id, reason, actor=actor)
            self.leases.revoke(goal_id)

    def observe_progress(
        self, goal_id: str, signals: set[str], event_id: str | None = None
    ) -> str:
        with exclusive_file_lock(self._goal_lock_path(goal_id)):
            if self.revocations.is_revoked(goal_id):
                return self.project_state(goal_id).status
            verified_signals: set[str] = set()
            if event_id:
                event = next(
                    (
                        item
                        for item in self._event_log.read_all()
                        if item.event_id == event_id and item.goal_id == goal_id
                    ),
                    None,
                )
                if event and self._event_is_authentic(event):
                    if event.action == "ARTIFACT_CHANGED" and "artifact_changed" in signals:
                        artifact = (self.workspace / event.data.get("artifact_path", "")).resolve()
                        contract = self.contracts.get(goal_id)
                        artifact_hash = event.data.get("artifact_hash", "")
                        if (
                            contract is not None
                            and artifact.is_relative_to(self.workspace)
                            and artifact.is_file()
                            and hashlib.sha256(artifact.read_bytes()).hexdigest()
                            == artifact_hash
                            and artifact.read_text(encoding="utf-8")
                            == contract.expected_content
                            and self._consume_progress_event(
                                goal_id, event_id, artifact_hash
                            )
                        ):
                            verified_signals.add("artifact_changed")
            self.progress.observe(ProgressInvariant(verified_signals), goal_id)
            if self.progress.should_stop(goal_id):
                self._append_event(
                    AuthorityEvent(
                        event_id=f"evt-{uuid.uuid4().hex}",
                        goal_id=goal_id,
                        actor="runtime",
                        action="GOAL_STATUS_CHANGED",
                        data={"to": "STOPPED_NO_PROGRESS"},
                    )
                )
                self.revocations.revoke(
                    goal_id, "no meaningful progress", actor="runtime"
                )
                self.leases.revoke(goal_id)
                return "STOPPED_NO_PROGRESS"
            return "ACTIVE"

    def _verify_artifact(
        self, event_id: str, capability: ReviewerCapability
    ) -> RuntimeVerification:
        goal_id = capability.goal_id
        with exclusive_file_lock(self._goal_lock_path(goal_id)):
            contract = self.contracts.get(goal_id)
            token_hash = hashlib.sha256(capability.secret.encode("utf-8")).hexdigest()
            if (
                contract is None
                or capability.reviewer_id != contract.reviewer_id
                or not hmac.compare_digest(token_hash, contract.reviewer_token_hash)
            ):
                return RuntimeVerification(
                    "VERIFICATION_FAILED",
                    JudgeDecision(False, "valid independent reviewer capability required"),
                    "",
                )
            state = self.project_state(goal_id)
            if state.status == "VERIFIED_COMPLETE":
                completion = next(
                    (
                        item
                        for item in reversed(self._event_log.read_all())
                        if item.goal_id == goal_id
                        and item.action == "GOAL_STATUS_CHANGED"
                        and item.data.get("to") == "VERIFIED_COMPLETE"
                        and self._event_is_authentic(item)
                    ),
                    None,
                )
                return RuntimeVerification(
                    "VERIFIED_COMPLETE",
                    JudgeDecision(True, "already verified"),
                    completion.data.get("artifact_hash", "") if completion else "",
                )
            if state.status in {
                "VERIFIED_STOPPED",
                "STOPPED_NO_PROGRESS",
                "RECONCILE_REQUIRED",
            }:
                return RuntimeVerification(
                    state.status,
                    JudgeDecision(False, "goal is terminal"),
                    "",
                )
            if self.revocations.is_revoked(goal_id):
                return RuntimeVerification(
                    "RECONCILE_REQUIRED",
                    JudgeDecision(False, "revocation has no matching terminal event"),
                    "",
                )
            lease = self.leases.get(goal_id)
            if lease and lease.writer == capability.reviewer_id:
                return RuntimeVerification(
                    "VERIFICATION_FAILED",
                    JudgeDecision(False, "writer cannot verify its own result"),
                    "",
                )
            source_event = next(
                (item for item in self._event_log.read_all() if item.event_id == event_id),
                None,
            )
            if (
                source_event is None
                or not self._event_is_authentic(source_event)
                or source_event.action != "ARTIFACT_CHANGED"
                or source_event.goal_id != goal_id
                or source_event.contract_hash != contract.contract_hash
                or source_event.data.get("artifact_path") != contract.artifact_path
            ):
                return RuntimeVerification(
                    "VERIFICATION_FAILED",
                    JudgeDecision(False, "evidence is not bound to an authentic authority event"),
                    "",
                )
            artifact = (self.workspace / contract.artifact_path).resolve()
            if (
                not artifact.is_relative_to(self.workspace)
                or not artifact.is_file()
                or hashlib.sha256(artifact.read_bytes()).hexdigest()
                != source_event.data.get("artifact_hash")
            ):
                return RuntimeVerification(
                    "VERIFICATION_FAILED",
                    JudgeDecision(False, "authority event artifact has changed"),
                    "",
                )
            record = self.evidence.verify_result(
                event_id,
                VerificationInput(
                    goal_id=goal_id,
                    outcome_id=contract.outcome_id,
                    scenario_id=contract.scenario_id,
                    artifact_path=contract.artifact_path,
                    contract_hash=contract.contract_hash,
                    expected_content=contract.expected_content,
                ),
                capability.reviewer_id,
            )
            decision = self.gate.evaluate(
                [record],
                goal_id=goal_id,
                contract_hash=contract.contract_hash,
                required_scenarios={contract.scenario_id},
            )
            status = "VERIFIED_COMPLETE" if decision.passed else "VERIFICATION_FAILED"
            if decision.passed:
                self._append_event(
                    AuthorityEvent(
                        event_id=f"evt-{uuid.uuid4().hex}",
                        goal_id=goal_id,
                        actor=capability.reviewer_id,
                        action="GOAL_STATUS_CHANGED",
                        contract_hash=contract.contract_hash,
                        data={
                            "to": status,
                            "event_id": record.event_id,
                            "outcome_id": record.outcome_id,
                            "scenario_id": record.scenario_id,
                            "artifact_path": record.artifact_path,
                            "artifact_hash": record.artifact_hash,
                            "verified_by": record.verified_by,
                        },
                    )
                )
                self.leases.revoke(goal_id)
            return RuntimeVerification(status, decision, record.artifact_hash)

    def project_state(self, goal_id: str | None = None) -> ProjectedState:
        events = [
            event
            for event in self._event_log.read_all()
            if self._event_is_authentic(event)
        ]
        if goal_id is None:
            goals = {event.goal_id for event in events}
            if len(goals) > 1:
                raise ValueError("goal_id is required for a multi-goal workspace")
            goal_id = next(iter(goals), "unknown")
        state = StateProjector().project(events, goal_id=goal_id)
        if state.status != "VERIFIED_COMPLETE":
            return state
        completion = next(
            (
                event
                for event in reversed(events)
                if event.goal_id == goal_id
                and event.action == "GOAL_STATUS_CHANGED"
                and event.data.get("to") == "VERIFIED_COMPLETE"
                and self._event_is_authentic(event)
            ),
            None,
        )
        if completion is None:
            state.status = "RECONCILE_REQUIRED"
            return state
        artifact = (self.workspace / completion.data.get("artifact_path", "")).resolve()
        expected_hash = completion.data.get("artifact_hash", "")
        if (
            not artifact.is_relative_to(self.workspace)
            or not artifact.is_file()
            or not expected_hash
            or hashlib.sha256(artifact.read_bytes()).hexdigest() != expected_hash
        ):
            state.status = "RECONCILE_REQUIRED"
        return state
