# Cross-project obstacle loop

This repository may receive reusable LoopLoopLoop defects discovered while the
runtime is operating in other projects. Project-specific product work remains
in its owning project; only a reproducible runtime, goal-selection, evidence,
review, gate, or integration defect belongs here.

## Managed intake sources

The current supervisory automation accepts evidence from these source tasks:

- `019f5ada-47c1-7d63-888e-327ff25861a5`
- `019f5ba5-9a4e-7d53-b6a3-d888fa01760c`
- `019f5a6d-f1cd-73b3-9a94-8d3b4683227a`

Adding a task to this list authorizes evidence intake, not cross-project writes
or copying private project data into this repository.

## Intake test

Create a ledger entry only when all of the following are true:

1. The obstacle prevents a valid LoopLoopLoop step, including framing a useful
   next goal, gathering direct evidence, running an independent review, or
   reaching a deterministic gate verdict.
2. The symptom and exact failure evidence are recorded with secrets and private
   content removed.
3. The failure is reproducible in this repository or is supported by evidence
   from at least two managed projects.
4. The proposed change improves the generic runtime rather than changing a
   business project's acceptance contract.

If no useful goal can be selected because a project is genuinely complete or
needs an owner decision, record that state only in the source project. Do not
copy it into this repository, invent work, or treat it as a runtime defect.

## Ledger

Append entries to `docs/cross-project-obstacles.md` using this minimum schema:

- UTC discovery time and source task ID;
- sanitized symptom and direct evidence paths;
- classification: `RUNTIME_DEFECT`, `GOAL_SELECTION_DEFECT`,
  `EVIDENCE_DEFECT`, `REVIEW_DEFECT`, or `GATE_DEFECT`;
- reproduction command or multi-project evidence;
- smallest shared root cause;
- changed files and verification commands;
- independent review and gate verdict;
- commit and push result.

Project-only obstacles are deduplicated in their source project's `.loop` or
`.looploop` state and never enter this repository's ledger.

## Repair and verification

Work in the dedicated `looplooploop` branch. Fix only the first shared root
cause. Run the narrow reproduction, the relevant test file, and the full local
test suite before promotion. A worker may not approve its own repair; a fresh
read-only review and adversarial challenge are required before the runtime gate
may mark it ready to commit.

Never copy business source code, assets, datasets, credentials, raw logs, or
customer content into this repository. Use minimal synthetic fixtures when a
regression test is needed.

## Two-hour Git synchronization

The supervisory automation checks every two hours. It may commit and push only
when all of these conditions hold:

1. the checkout is `C:\Users\Administrator\Documents\codex-loop-looplooploop`;
2. the current branch is exactly `looplooploop`;
3. `origin` is exactly `https://github.com/M-sea-art/loop-loop-loop.git`;
4. every staged path belongs to a ledgered, independently verified skill fix;
5. required tests pass and the ledger is updated;
6. no unresolved merge, rebase, conflict, credential, or release gate exists.

Stage explicit paths only. Never use `git add -A`, never create empty commits,
never force-push, and never rewrite remote history. A clean two-hour window is a
successful no-op. Authentication, network, divergence, or branch-protection
failure must be recorded exactly and left for user action; do not retry in a
loop or request credentials.

This exception authorizes commit and push only to `origin/looplooploop` in this
skill repository. It does not authorize commits, pushes, merges, releases, or
deployments in any managed business project.
