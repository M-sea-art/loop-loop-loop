"""Runtime mutation guard.

Central place for future executor integration. Mutation requires both a valid
writer lease and absence of a persistent revoke decision.
"""


class MutationDenied(Exception):
    pass


class RuntimeMutationGuard:
    def __init__(self, lease_validator, revocation_registry):
        self.lease_validator = lease_validator
        self.revocation_registry = revocation_registry

    def check_write(self, goal_id: str, writer: str, lease) -> bool:
        if self.revocation_registry.is_revoked(goal_id):
            raise MutationDenied("goal has been revoked")

        if not self.lease_validator.validate(lease, writer):
            raise MutationDenied("writer lease is invalid")

        return True
