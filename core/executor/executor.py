"""Minimal LoopLoopLoop executor.

The executor turns a planned action into an execution record.
It deliberately does not mark goals complete.
Completion requires independent verification.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from core.planner.planner import PlanStep


@dataclass
class ExecutionResult:
    action: str
    status: str
    output: Any = None
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


class Executor:
    """Execute the minimal, explicitly planned file action."""

    def __init__(self, workspace: Path | str):
        self.workspace = Path(workspace).resolve()

    def _target_path(self, relative_path: str) -> Path:
        target = (self.workspace / relative_path).resolve()
        if not target.is_relative_to(self.workspace):
            raise ValueError("execution target must stay inside the workspace")
        return target

    def execute(self, step: PlanStep) -> ExecutionResult:
        if step.action != "write_file":
            return ExecutionResult(action=step.action, status="REJECTED")

        target = self._target_path(step.target_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(step.content, encoding="utf-8")
        return ExecutionResult(
            action=step.action,
            status="EXECUTED",
            output={"artifact": step.target_path},
        )
