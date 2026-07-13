"""Goal-to-execution planning boundary."""

from __future__ import annotations

from dataclasses import dataclass

from core.goal.goal_contract import GoalContract


@dataclass(frozen=True)
class PlanStep:
    action: str
    target_path: str
    content: str


class Planner:
    def create_plan(self, goal: GoalContract) -> list[PlanStep]:
        if not goal.is_well_defined():
            raise ValueError("cannot plan an incomplete goal contract")
        return [
            PlanStep(
                action="write_file",
                target_path=goal.target_path,
                content=goal.expected_content,
            )
        ]
