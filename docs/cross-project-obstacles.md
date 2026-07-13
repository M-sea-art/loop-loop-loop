# Cross-project obstacle ledger

Append-only ledger for reusable LoopLoopLoop defects admitted by
`docs/cross-project-obstacle-loop.md`.

## Bootstrap — 2026-07-14

- Source tasks: `019f5ada-47c1-7d63-888e-327ff25861a5`,
  `019f5ba5-9a4e-7d53-b6a3-d888fa01760c`, and
  `019f5a6d-f1cd-73b3-9a94-8d3b4683227a`.
- Classification: `GOVERNANCE_SETUP` (not counted as a runtime defect).
- Symptom: no isolated, authoritative Git branch existed for safely collecting
  generic runtime repairs without staging pre-existing business or user work.
- Shared root cause: the installed plugin kit was not a Git checkout and the
  historical source checkout had unrelated uncommitted changes.
- Repair: establish a clean worktree on branch `looplooploop`, define strict
  intake rules, and restrict scheduled Git synchronization to verified explicit
  paths in that worktree.
- Direct evidence: source checkout reported existing modified/untracked files;
  installed kit reported no `.git`; the dedicated worktree started from remote
  `main` commit `bef96e50999418610fccc008655994e640e8fdbd`.
- Verification: documentation links resolve; branch and remote checks are part
  of the explicit pre-push gate.
- Status: `PASS` after the independent review required the project-only ledger
  boundary to be tightened.

## Windows artifact containment — 2026-07-14

- Source task: supervisory validation for
  `019f5ba5-9a4e-7d53-b6a3-d888fa01760c` and the other managed tasks.
- Classification: `EVIDENCE_DEFECT`.
- Symptom: 10 of 18 repository tests failed with
  `evidence artifact must be an existing file inside the project` on Windows.
- Reproduction: `python -m unittest discover -s tests -v` from the clean branch
  worktree.
- Shared root cause: `relative_artifact` compared a resolved long-form artifact
  path against an unresolved 8.3 short-form project path returned by
  `tempfile.TemporaryDirectory`.
- Repair: resolve the project root once, then perform both absolute and relative
  artifact containment checks against that canonical root.
- Changed file: `scripts/loop.py`.
- Verification: `python -m unittest discover -s tests -v` passed 18/18;
  `python examples/simple_goal/run_example.py` exited 0 with
  `VERIFIED_COMPLETE`; `git diff --check` passed.
- Adversarial challenge: repository-contained relative and absolute artifacts
  were accepted, while `../AGENTS.md` and
  `C:\Windows\System32\drivers\etc\hosts` were rejected.
- Independent review: code fix PASS; the initial governance draft was
  `NOT_COMPLETE` until project-only entries were forbidden from the central
  ledger. No credentials, private project content, or containment regression
  were found.
- Gate: `PASS` after the governance correction and one final verification run.
