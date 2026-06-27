# Recovery Engine

Start from the last durable state, not memory.

Read `.loop/STATE.md` first. If missing, initialize with `scripts/loop.py init`.

If a previous run stopped:

- continue from `next_run_instruction`
- preserve blockers
- do not redo completed evidence unless stale
- keep scope inside `.loop/GOAL.md`

If state conflicts with the repository, trust the repository and repair state.
