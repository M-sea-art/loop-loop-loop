"""Bounded work contracts and results for optional collaboration."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TaskContract:
    contract_id: str
    goal: str
    required_capabilities: tuple[str, ...]
    inputs: tuple[str, ...]
    allowed_actions: tuple[str, ...]
    forbidden_actions: tuple[str, ...]
    expected_outputs: tuple[str, ...]
    evidence_requirements: tuple[str, ...]

    def __post_init__(self) -> None:
        required_text = {
            "contract_id": self.contract_id,
            "goal": self.goal,
        }
        for name, value in required_text.items():
            if not value.strip():
                raise ValueError(f"{name} must not be empty")
        if not self.expected_outputs:
            raise ValueError("expected_outputs must not be empty")
        if not self.evidence_requirements:
            raise ValueError("evidence_requirements must not be empty")
        collections = {
            "required_capabilities": self.required_capabilities,
            "inputs": self.inputs,
            "allowed_actions": self.allowed_actions,
            "forbidden_actions": self.forbidden_actions,
            "expected_outputs": self.expected_outputs,
            "evidence_requirements": self.evidence_requirements,
        }
        for name, values in collections.items():
            if any(not item.strip() for item in values):
                raise ValueError(f"{name} cannot contain empty values")
        overlap = set(self.allowed_actions) & set(self.forbidden_actions)
        if overlap:
            raise ValueError(f"actions cannot be both allowed and forbidden: {sorted(overlap)}")


@dataclass(frozen=True)
class AgentResult:
    contract_id: str
    status: str
    outputs: tuple[str, ...] = ()
    evidence_refs: tuple[str, ...] = ()
    notes: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.status not in {"COMPLETED", "BLOCKED", "FAILED"}:
            raise ValueError("status must be COMPLETED, BLOCKED, or FAILED")
        if self.status == "COMPLETED" and (not self.outputs or not self.evidence_refs):
            raise ValueError("completed results require outputs and evidence_refs")
