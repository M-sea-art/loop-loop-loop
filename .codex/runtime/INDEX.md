# Runtime Index

This is the Codex Loop Runtime. Keep the live prompt short and route behavior through these files.

## Load Order

1. `orchestrator.md`
2. `recovery.md`
3. `capability.md`
4. `agent-factory.md`
5. `verification.md`
6. `acceptance.md`
7. `experience.md`

## One Loop

Recover state, discover the highest-value next action, execute it, verify it, accept or reject it, then record what changed.

Every run must update `.loop/STATE.md`.
Every run must write a report under `.loop/reports/` and return the shape in `loop_result.schema.json`.

## Status

- `CANDIDATE_PASS`: acceptance passed with evidence.
- `CANDIDATE_PARTIAL`: useful progress, not enough evidence or score.
- `CANDIDATE_REJECTED`: attempted path failed, another route exists.
- `CANDIDATE_BLOCKED`: no safe next action without human input.
