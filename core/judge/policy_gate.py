"""Deterministic completion gate."""


class PolicyGate:
    def evaluate(self, goal, evidence, review_passed=False):
        if not evidence:
            return False

        if not review_passed:
            return False

        return bool(goal)
