# loop loop loop

**It doesn't stop until the result is independently verified.**

`loop loop loop` is a small Codex Loop Runtime. The prompt starts the runtime; durable contracts, evidence, independent review, and a policy gate own completion.

```text
Goal
  -> Independent Framing
  -> Frozen Acceptance Contract
  -> Worker
  -> Direct Evidence Ledger
  -> Independent Read-only Review
  -> Adversarial Challenge
  -> Deterministic Policy Gate
  -> Experience
```

## Why this upgrade exists

A build can pass while the product fails. Tests can pass while their rubric misses the user's real outcome. A maker can generate many screenshots or logs without actually inspecting what they prove.

Loop therefore treats process metrics as supporting signals, not acceptance. A worker can implement and verify, but cannot approve itself. `CANDIDATE_PASS` is available only after direct evidence, a fresh read-only review, challenge coverage, and the policy gate agree on the same frozen workspace.

## Quick start

```bash
git clone https://github.com/M-sea-art/loop-loop-loop.git
cd loop-loop-loop
python scripts/loop.py install C:\path\to\your\project
```

In the target project:

```bash
# 1. Define the real goal in .loop/GOAL.md
python scripts/loop.py frame .

# Or edit the draft contract and freeze it explicitly
python scripts/loop.py freeze-contract .

# 2. Run one worker loop
python scripts/loop.py run .

# 3. Record direct claim/scenario evidence
python scripts/loop.py record-evidence . \
  --claim-id OUT-001 \
  --scenario-id SCN-001 \
  --evidence-type test \
  --artifact .loop/evidence/test-output.txt \
  --notes "Behavioral test passed"

# 4. Run a fresh read-only review and the deterministic gate
python scripts/loop.py review .
python scripts/loop.py gate .

# Or orchestrate the full sequence
python scripts/loop.py run-loop . --max-iterations 10
```

Inspect prompts without invoking Codex:

```bash
CODEX_DRY_RUN=1 python scripts/loop.py frame .
CODEX_DRY_RUN=1 python scripts/loop.py run .
CODEX_DRY_RUN=1 python scripts/loop.py review .
```

## Runtime shape

```text
.codex/runtime/
  INDEX.md
  orchestrator.md
  recovery.md
  capability.md
  agent-factory.md
  contract.md
  verification.md
  observation.md
  challenge.md
  acceptance.md
  experience.md
  acceptance_contract.schema.json
  loop_result.schema.json
  review_result.schema.json

.loop/
  GOAL.md
  GOALS.md
  ACCEPTANCE_CONTRACT.json
  contract.lock.json
  EVIDENCE_LEDGER.jsonl
  REPORT.md
  REVIEW.md
  ACCEPTANCE.md
  FAILURE_PATTERNS.md
  reviews/
  evidence/
  reports/
```

## Lifecycle

| State | Meaning | Who can produce it |
| --- | --- | --- |
| `CONTRACT_DRAFT` | Real outcomes are not frozen | framer / human |
| `IMPLEMENTED` | Candidate implementation exists | worker |
| `AUTOMATION_VERIFIED` | Worker checks and direct evidence coverage are complete | worker + runtime |
| `REVIEW_FAILED` | Independent review or challenge found a material gap | reviewer + gate |
| `NEEDS_HUMAN` | Automated and independent gates passed, but risk requires a person | gate |
| `INDEPENDENTLY_VERIFIED` | Frozen contract, direct evidence, review, and challenge all pass | policy gate |

The worker schema has no acceptance field and cannot return `CANDIDATE_PASS`.

## What the gate checks

- contract and policy hashes have not changed;
- every required outcome/scenario pair has a valid evidence record;
- evidence artifacts exist and still match their hashes;
- evidence types match the artifact modality;
- review came from a separate read-only Codex execution;
- review covered every required pair;
- no P0/P1 finding remains;
- at least one passing challenge exists for every modality;
- the review matches the current workspace and ledger fingerprints;
- risk-based human approval is respected.

## Failure patterns

The runtime starts with reusable patterns learned from real false-completion failures:

- `PROXY_PASS_REALITY_FAIL`
- `SELF_CERTIFIED_COMPLETION`
- `RUBRIC_DRIFT`
- `STATE_COVERAGE_GAP`
- `PERCEPTUAL_BLINDNESS`
- `SEMANTIC_SCOPE_CONFLICT`
- `EVIDENCE_QUANTITY_FALLACY`
- `PREMATURE_COMPLETION`

The goal is not to hard-code one UX checklist. It is to prevent any artifact from being accepted through self-certification or proxy metrics.

## Commands

- `install <project>`: install runtime, templates, skill, and scripts.
- `init <project>`: initialize state directories and missing templates.
- `frame <project>`: use a separate read-only framing process to create and freeze the contract.
- `freeze-contract <project>`: validate and freeze an explicitly edited contract.
- `record-evidence <project>`: append a hash-bound direct evidence record.
- `run <project>`: run one worker loop.
- `score <project>`: show diagnostic scores and evidence coverage; never promotes acceptance.
- `review <project>`: run a fresh read-only independent reviewer and challenge.
- `gate <project>`: apply deterministic promotion policy.
- `run-loop <project>`: orchestrate worker, review, gate, and repair iterations.
- `check <project>`: validate runtime files, schemas, state, secrets, and contract health.
- `discover <project>`: refresh local capabilities.
- `distill-experience <project>`: produce reviewed candidate skills from repeated lessons.
