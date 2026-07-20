# Runtime Index

This is the Loop evidence-gated runtime. The prompt starts the runtime; durable policy files own the loop.

## Load Order

1. `orchestrator.md`
2. `recovery.md`
3. `adaptive-execution.md`
4. `capability.md`
5. `agent-factory.md`
6. `contract.md`
7. `verification.md`
8. `observation.md`
9. `challenge.md`
10. `acceptance.md`
11. `experience.md`

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

## Execution Mode Boundary

The normal loop uses the current Codex agent. Complexity analysis is advisory;
only explicit user authorization may raise the collaboration ceiling. Any
collaboration uses Codex-native delegation and preserves the active Codex
configuration and permission model.
