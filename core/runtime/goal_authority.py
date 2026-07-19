"""Frozen goal contracts and opaque independent-review capabilities."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
from pathlib import Path
import secrets

from core.storage_lock import exclusive_file_lock


@dataclass(frozen=True)
class FrozenGoalContract:
    goal_id: str
    contract_hash: str
    outcome_id: str
    scenario_id: str
    artifact_path: str
    expected_content: str
    reviewer_id: str
    reviewer_token_hash: str


@dataclass(frozen=True)
class ReviewerCapability:
    """Secret capability delivered to the reviewer, never to the writer runtime."""

    goal_id: str
    reviewer_id: str
    secret: str


class GoalContractStore:
    def __init__(self, path: str | Path):
        self.path = Path(path)

    def _load(self) -> dict[str, dict]:
        if not self.path.exists():
            return {}
        payload = json.loads(self.path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ValueError("goal contract store must be a JSON object")
        return payload

    def get(self, goal_id: str) -> FrozenGoalContract | None:
        payload = self._load().get(goal_id)
        return FrozenGoalContract(**payload) if payload else None

    def freeze(self, contract: FrozenGoalContract) -> FrozenGoalContract:
        with exclusive_file_lock(self.path):
            payload = self._load()
            existing = payload.get(contract.goal_id)
            serialized = asdict(contract)
            if existing is not None:
                if existing != serialized:
                    raise RuntimeError("goal contract is already frozen")
                return FrozenGoalContract(**existing)
            payload[contract.goal_id] = serialized
            self.path.parent.mkdir(parents=True, exist_ok=True)
            temporary = self.path.with_suffix(self.path.suffix + ".tmp")
            temporary.write_text(json.dumps(payload, sort_keys=True), encoding="utf-8")
            temporary.replace(self.path)
            return contract


class GoalAuthority:
    """Trusted coordinator boundary used before a writer is started."""

    def __init__(self, workspace: str | Path):
        workspace = Path(workspace).resolve()
        self._store = GoalContractStore(
            workspace / ".loop" / "reliability" / "contracts.json"
        )

    def freeze(
        self,
        *,
        goal_id: str,
        contract_hash: str,
        outcome_id: str,
        scenario_id: str,
        artifact_path: str,
        expected_content: str,
        reviewer_id: str = "independent-reviewer",
    ) -> ReviewerCapability:
        if not all(
            value
            for value in (
                goal_id,
                contract_hash,
                outcome_id,
                scenario_id,
                artifact_path,
                reviewer_id,
            )
        ):
            raise ValueError("frozen goal contract fields are required")
        secret = secrets.token_urlsafe(32)
        token_hash = hashlib.sha256(secret.encode("utf-8")).hexdigest()
        contract = FrozenGoalContract(
            goal_id=goal_id,
            contract_hash=contract_hash,
            outcome_id=outcome_id,
            scenario_id=scenario_id,
            artifact_path=artifact_path,
            expected_content=expected_content,
            reviewer_id=reviewer_id,
            reviewer_token_hash=token_hash,
        )
        self._store.freeze(contract)
        return ReviewerCapability(goal_id, reviewer_id, secret)

