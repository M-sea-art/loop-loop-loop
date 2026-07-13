"""Goal to execution planning boundary."""


class Planner:
    def create_plan(self, goal):
        return {
            "objective": goal.objective,
            "acceptance": goal.acceptance_criteria,
            "constraints": goal.constraints,
        }
