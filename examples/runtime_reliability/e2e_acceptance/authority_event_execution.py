"""Authority event execution wiring example.

This is the integration boundary between a runtime action and the
append-only authority model.
"""


def execute_goal_event(goal_id: str):
    return {
        "goal_id": goal_id,
        "event_recorded": True,
        "authority_source": "event_log",
    }
