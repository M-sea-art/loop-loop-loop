import unittest

from core.lease.revocation import RevocationRegistry


class StopProtocolTests(unittest.TestCase):
    def test_revocation_blocks_recovery(self):
        registry = RevocationRegistry()
        registry.revoke("goal-1", "human stop request")

        self.assertTrue(registry.is_revoked("goal-1"))
        self.assertIsNotNone(registry.get("goal-1"))


if __name__ == "__main__":
    unittest.main()
