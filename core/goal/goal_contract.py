"""LoopLoopLoop goal contract primitives.

A goal describes the desired outcome, not merely implementation tasks.
"""

from dataclasses import dataclass, field
from typing import List


@dataclass
class GoalContract:
    objective: str
    desired_state: str
    acceptance_criteria: List[str] = field(default_factory=list)
    constraints: List[str] = field(default_factory=list)

    def is_well_defined(self) -> bool:
        return bool(self.objective and self.desired_state and self.acceptance_criteria)
