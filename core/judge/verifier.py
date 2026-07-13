"""Independent verification gate."""


class VerificationResult:
    def __init__(self, passed: bool, reasons=None):
        self.passed = passed
        self.reasons = reasons or []


class Judge:
    def verify(self, goal, evidence):
        if not goal.is_well_defined():
            return VerificationResult(False, ["invalid goal contract"])
        if not evidence.all_verified():
            return VerificationResult(False, ["missing verified evidence"])
        return VerificationResult(True)
