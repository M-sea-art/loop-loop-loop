"""Minimal LoopLoopLoop executor.

The executor turns a planned action into an execution record.
It deliberately does not mark goals complete.
Completion requires independent verification.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass
class ExecutionResult:
    action: str
    status: str
    output: Any = None
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


class Executor:
    """Minimal execution boundary."""

    def execute(self, action: str, payload: Any = None) -> ExecutionResult:
        return ExecutionResult(
            action=action,
            status="EXECUTED",
            output=payload,
        )
