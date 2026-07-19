"""Unified runtime context for goal execution.

Runtime components should receive shared authority information instead of
reconstructing assumptions independently.
"""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class RuntimeContext:
    goal_id: str
    contract_hash: str = ""
    writer_id: str = ""
    lease: Any = None
    authority_state: Any = None
    evidence_scope: list[str] = field(default_factory=list)
