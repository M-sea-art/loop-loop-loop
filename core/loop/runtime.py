"""Minimal autonomous goal completion loop.

Flow:
Goal -> Plan -> Execute -> Verify

The runtime coordinates only. It never self-approves completion.
"""


class LoopRuntime:
    def __init__(self, planner, executor, judge):
        self.planner = planner
        self.executor = executor
        self.judge = judge

    def run_once(self, goal):
        plan = self.planner.create_plan(goal)
        results = [self.executor.execute(step) for step in plan]
        return self.judge.verify(goal, results)
