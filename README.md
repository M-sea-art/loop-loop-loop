# loop loop loop

**Autonomous Goal Completion Engine — it doesn't stop until the result is independently verified.**

`loop loop loop` is a small Codex Loop Runtime designed around one fundamental user need:

> AI should understand a desired outcome, define a complete goal, execute continuously, verify reality, and improve until the goal is truly achieved.

## Core Model

```text
Human Intent
      ↓
Goal Architect
      ↓
Frozen Acceptance Contract
      ↓
Planner
      ↓
Worker
      ↓
Evidence Ledger
      ↓
Independent Judge
      ↓
Policy Gate
      ↓
Verified Experience
```

## Design Philosophy

LoopLoopLoop is not a virtual company simulator.

The system does not become better by adding more departments, agents, or ceremony.

Every capability must improve one of:

- higher goal completion reliability;
- stronger verification;
- less human intervention.

## Why this exists

A build can pass while the product fails.

A worker can create artifacts without proving they solve the original problem.

Therefore:

- workers execute;
- judges verify;
- policy gates decide completion.

No agent can approve its own work.

## Runtime Flow

```text
Goal
 → Independent Framing
 → Acceptance Contract
 → Execution
 → Direct Evidence
 → Read-only Review
 → Challenge
 → Gate
 → Completion or Improvement Loop
```

## Quick Start

```bash
git clone https://github.com/M-sea-art/loop-loop-loop.git
cd loop-loop-loop
python scripts/loop.py install C:\path\to\your\project
```

Define the real goal:

```bash
python scripts/loop.py frame .
```

Run execution:

```bash
python scripts/loop.py run-loop . --max-iterations 10
```

Run the minimal end-to-end goal demo:

```bash
python examples/simple_goal/run_example.py
```

The demo reads `examples/simple_goal/GOAL.md`, creates the requested file in a
temporary workspace, collects direct file evidence, independently re-reads the
artifact, and prints `VERIFIED_COMPLETE` only after the policy gate passes.

## Core Documents

- `docs/looplooploop-v2-vision.md` — product direction and constraints
- `.loop/GOAL.md` — desired outcome
- `.loop/PLAN.md` — ordered execution plan
- `.loop/EVIDENCE.md` — evidence requirements and observations
- `.loop/ACCEPTANCE_CONTRACT.json` — frozen acceptance rules
- `.loop/EVIDENCE_LEDGER.jsonl` — direct evidence

## Completion Standard

Completion is not:

- code exists;
- tests pass;
- an agent says done.

Completion is:

- goal contract satisfied;
- evidence recorded;
- independent review passed;
- policy gate approved.

## Future Direction

LoopLoopLoop stays focused:

**Turn human intent into verified outcomes.**
