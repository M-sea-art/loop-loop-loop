"""Authority-aware runtime commit helper."""


class RuntimeCommit:
    def __init__(self, guard, event_log):
        self.guard = guard
        self.event_log = event_log

    def commit_mutation(self, goal_id: str, writer: str, event):
        decision = self.guard.can_mutate(goal_id, writer)
        if not decision.allowed:
            raise PermissionError(decision.reason)

        return self.event_log.append(event)
