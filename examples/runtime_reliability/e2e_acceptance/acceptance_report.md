# Runtime Reliability v1 Acceptance Report

Test date: 2026-07-19

Branch: `feat/runtime-reliability-v1`

Baseline commit: `a93c7524f0379c2acd0255d5313cb67b8274b9b2`

## Executive result

The original branch produced a false green result: `unittest` discovered only
18 legacy tests while pytest-style reliability files and constant-return E2E
scenarios did not execute meaningful behavior. Those placeholders were replaced
with standard-library `unittest` cases that exercise real files, durable state,
authority events, and rejection paths.

Current local result: **63/63 tests passed**. The four required E2E scenarios,
the production `LoopRuntime` simple-goal path, compilation, and whitespace
validation all pass. A clean, non-committing merge with adaptive-routing commit
`23bf5110c77398840920d28ab0671e76e5ba86ae` passes **78/78 tests**.

## Required scenarios

| Scenario | Observed result | Evidence |
| --- | --- | --- |
| Successful goal | `VERIFIED_COMPLETE` | Frozen contract, writer lease, signed `ARTIFACT_CHANGED`, real artifact hash, independent reviewer capability, goal-scoped projection |
| Human revoke | `VERIFIED_STOPPED` | Durable revoke, lease removal, runtime reconstruction, future mutation rejected |
| No progress | `STOPPED_NO_PROGRESS` | Activity signals do not reset the counter; unchanged content creates no event; only a fresh matching artifact hash can be consumed once |
| Writer conflict | `SECOND_WRITER_REJECTED` | Cross-instance locking allows exactly one active writer |

Command:

```bash
python examples/runtime_reliability/run_all_scenarios.py
```

Observed output:

```text
success_case: VERIFIED_COMPLETE
revoke_case: VERIFIED_STOPPED
no_progress_case: STOPPED_NO_PROGRESS
writer_conflict_case: SECOND_WRITER_REJECTED
```

## Reliability invariant coverage

| Invariant | Behavioral coverage | Result |
| --- | --- | --- |
| Valid lease required for mutation | missing/wrong/expired/read-only writer, contract/path mismatch, commit rollback on log failure | PASS |
| One writer per goal | threads, pre-created runtime instances, writer conflict E2E | PASS |
| Stop cannot be bypassed | old writer, second runtime, reconstruction, commit/revoke race, revoke-log failure and retry | PASS |
| Activity is not progress | heartbeat/report/agent activity, repeated event, repeated hash, unchanged commit, persisted counters, cross-goal concurrent updates | PASS |
| Only complete independent evidence can finish | frozen contract, opaque reviewer capability, signed event binding, fabricated event, alias/self-review, wrong content, artifact replacement, replay-idempotent completion | PASS |

Additional recovery coverage includes corrupt JSONL tails, duplicate event IDs,
stale lock recovery, goal-scoped projection, projection reconstruction,
post-completion mutation rejection, and artifact rollback.

## Production and upgrade compatibility

`LoopRuntime.run_once()` now reaches `GoalLifecycle`, which freezes the goal,
acquires a writer lease, commits through `ReliabilityRuntime`, and completes only
through `ArtifactReviewer`. The legacy direct `Executor` remains available as a
unit-level primitive but is no longer used by the production lifecycle.

Validation commands:

```bash
python -W error -m unittest discover -s tests -q
python -m compileall -q core scripts tests examples
python examples/simple_goal/run_example.py --workspace <empty-temp-dir>
git diff --check
```

Adaptive-routing compatibility was tested in an isolated copy with a clean
`git merge --no-commit --no-ff origin/feat/codex-adaptive-routing`. The combined
suite passed 78/78, all four reliability scenarios passed, and the simple-goal
production demo reached `VERIFIED_COMPLETE`. No merge commit was created.

## Independent review history

The independent reviewer initially rejected the branch despite green tests and
found production-path bypass, commit/revoke TOCTOU, caller-selected evidence,
event injection, cross-goal projection, non-closed terminal state, stale locks,
and spoofable progress. A second review found unchanged-artifact progress,
shared progress-store races, completion replay, and revoke failure split state.
Each finding now has a production fix and a regression test. Final reviewer Gate
is recorded below after the last read-only rerun.

## Residual limitations

- The lock-file implementation targets processes sharing a local filesystem;
  distributed/network filesystems require a transactional store.
- The v1 end-to-end contract supports one frozen scenario and one exact-text
  artifact; multi-artifact and non-text acceptance belong to a later version.
- Authority signatures and reviewer capabilities protect runtime interfaces and
  accidental injection inside this process model; they are not a substitute for
  OS-level isolation against a process that can read all workspace secrets.
- The environment does not include the `coverage` package. Coverage is therefore
  reported as explicit invariant/branch cases rather than a line percentage.

## Gate

**PASS.** The final read-only independent review reran 63/63 tests, the four
E2E scenarios, the production path, compilation, and diff validation. It also
reproduced the prior failure cases after their fixes: unchanged commits create
no event, progress events cannot be replayed, two-goal progress updates remain
atomic across ten stress rounds, completion review is idempotent, and a failed
revoke event append leaves no split state. The reviewer reported no remaining
P0 or P1 defects and approved the implementation for the commit/merge workflow.
