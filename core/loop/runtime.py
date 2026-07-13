"""Public runtime facade for the goal lifecycle."""

from __future__ import annotations

from pathlib import Path

from core.goal.lifecycle import GoalLifecycle, GoalRunResult


class LoopRuntime:
    def __init__(self, workspace: Path | str):
        self.lifecycle = GoalLifecycle(workspace)

    def run_once(self, goal_file: Path | str) -> GoalRunResult:
        return self.lifecycle.run(goal_file)
