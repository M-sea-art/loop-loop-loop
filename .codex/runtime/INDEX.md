# Runtime Index

This is the Loop evidence-gated runtime. The prompt starts the runtime; durable policy files own the loop.

## Load Order

1. `orchestrator.md`
2. `recovery.md`
3. `capability.md`
4. `agent-factory.md`
5. `contract.md`
6. `verification.md`
7. `observation.md`
8. `challenge.md`
9. `acceptance.md`
10. `experience.md`

## One Loop

```text
Recover -> Frame/Freeze -> Pick -> Execute -> Observe -> Verify -> Independent Review -> Challenge -> Gate -> Record
```

`GOAL.md` owns intent. `ACCEPTANCE_CONTRACT.json` owns frozen observable outcomes. `EVIDENCE_LEDGER.jsonl` binds claims to direct evidence. Worker reports never own acceptance.

## Promotion Boundary

- Worker: at most `AUTOMATION_VERIFIED`.
- Separate read-only reviewer: may return review `PASS`, `FAIL`, or `BLOCKED`.
- Policy gate: may return `INDEPENDENTLY_VERIFIED` or a non-passing lifecycle state.
- Human: owns release, merge, deploy, destructive, credential, payment, and risk-based approval gates.

No score, build, log, screenshot count, or worker declaration can directly produce `CANDIDATE_PASS`.
