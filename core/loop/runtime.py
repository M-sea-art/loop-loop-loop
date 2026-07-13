"""Minimal autonomous goal completion loop."""


class LoopRuntime:
    def __init__(self, planner, executor, judge):
        self.planner = planner
        self.executor = executor
        self.judge = judge

    def run_once(self, goal):
        plan = self.planner.create_plan(goal)
        result = self.executor.execute(plan)
        return self.judge.verify(goal, result)
