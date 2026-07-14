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

## Append-only ledger current-contract recovery — 2026-07-14

- Discovery time: `2026-07-14T00:10:00Z`.
- Source tasks: `019f5ba5-9a4e-7d53-b6a3-d888fa01760c` and
  `019f5a6d-f1cd-73b3-9a94-8d3b4683227a`.
- Classification: `GATE_DEFECT`.
- Sanitized symptom: a current contract with complete direct PASS evidence was
  kept at `NEEDS_EVIDENCE` because append-only ledger rows from an older
  contract hash and earlier current-contract FAIL observations were counted as
  permanently invalid.
- Direct evidence: the voice project gate reported historical failures in
  `.loop/EVIDENCE_LEDGER.jsonl` as blocking despite current release and mobile
  summaries passing; the dashboard project reproduced the same condition and
  reached `missing_pairs=[]`, `modality_missing=[]`, `invalid_records=[]` only
  after filtering history from current-contract coverage.
- Reproduction: append one old-contract PASS row and one current-contract FAIL
  row after two valid current-contract PASS rows, then call
  `evaluate_evidence_coverage`; the unfixed runtime returned `complete=false`.
- Shared root cause: `evaluate_evidence_coverage` validated every append-only
  row against the current lock before separating historical and nonpassing
  observations from candidate PASS evidence.
- Repair: preserve old-contract rows in `historical_records` and current
  non-PASS rows in `nonpassing_records`, but compute current coverage and
  blocking `invalid_records` only from current-contract PASS candidates.
- Changed files: `scripts/loop.py`, `tests/test_runtime.py`, and this ledger.
- Verification: the focused regression passed; full local suite passed 19/19.
  Existing tampered-current-artifact coverage remains green and still blocks.
- Automatic access approval: initialized the skill repository's local
  CodeGraph index with `codegraph init -i` because structural inspection was
  otherwise unavailable; result was 15 files, 240 nodes, 225 edges. The
  generated `.codegraph/` directory is local-only and is not an authorized
  commit path.
- Independent review and adversarial challenge: initial verdict `NOT_COMPLETE`;
  malformed rows missing `contract_hash` or `result` were incorrectly
  downgraded before structural validation. After the correction, fresh review
  returned `PASS`: missing discriminators, invalid JSON, current artifact
  tampering, wrong evidence types, modality mismatch, and missing pairs all
  remain blocking; valid old-contract PASS and valid current-contract FAIL rows
  remain visible without poisoning current PASS coverage.
- Gate: `PASS`; focused reproduction and full suite passed 19/19, independent
  challenge passed, and `git diff --check` passed.
- Commit and push: `PASS`; verified repair committed as `328b377` and pushed
  with `git push origin HEAD:refs/heads/looplooploop` during the
  `2026-07-14T01:51Z` sync window.
