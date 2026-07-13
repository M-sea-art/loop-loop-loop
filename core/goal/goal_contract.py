"""LoopLoopLoop goal contract primitives.

A goal describes the desired outcome, not merely implementation tasks.
"""

from dataclasses import dataclass, field
from typing import List


@dataclass
class GoalContract:
    objective: str
    desired_state: str
    target_path: str
    expected_content: str
    acceptance_criteria: List[str] = field(default_factory=list)
    constraints: List[str] = field(default_factory=list)

    def is_well_defined(self) -> bool:
        return bool(
            self.objective.strip()
            and self.desired_state.strip()
            and self.target_path.strip()
            and self.expected_content
            and self.acceptance_criteria
            and all(item.strip() for item in self.acceptance_criteria)
        )
