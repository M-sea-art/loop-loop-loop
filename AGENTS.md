# loop loop loop

Use the runtime; do not expand a giant prompt.

```text
Recover -> Frame/Freeze -> Execute -> Observe -> Verify -> Independent Review -> Challenge -> Gate -> Record
```

Hard gates:

- The acceptance contract and policy are frozen before implementation.
- The worker may not modify the contract, policy, reviews, or weaken checks.
- The worker cannot emit `CANDIDATE_PASS`.
- A separate read-only reviewer must inspect actual artifacts and direct evidence.
- The policy gate rejects contract drift, policy drift, stale review, missing scenario coverage, and changed evidence.
- Human approval remains required for release, merge, deploy, payment, credentials, destructive action, and configured risk gates.
