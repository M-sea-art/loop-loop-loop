# LoopLoopLoop Runtime Foundation v2

## Purpose

LoopLoopLoop is an autonomous goal completion engine.

The system optimizes one outcome:

> AI understands a meaningful goal, defines completion, executes work, verifies reality, and improves until the desired state is achieved.

## Core Runtime

```
Goal
 ↓
Planner
 ↓
Executor
 ↓
Evidence Collector
 ↓
Independent Judge
 ↓
Improvement Loop
 ↓
Verified Completion
```

## Design Boundary

Do not add complexity unless it measurably improves:

1. Goal completion probability
2. Failure reduction
3. Reduction of human intervention

## Non Goals

- Simulating companies
- Creating unnecessary agent hierarchies
- Optimizing reports instead of outcomes
- Declaring completion without evidence

## Implemented Foundation

- Goal Contract
- Planner
- Executor
- Evidence Ledger
- Independent Judge
- Policy Gate
- Goal Lifecycle
- End-to-End Goal Demo

The reference demo proves one deliberately narrow goal: create a file whose
content exactly matches the goal contract. The executor cannot declare success;
the collector reads the artifact directly, the judge re-reads it and rejects
stale evidence, and only the policy gate returns `VERIFIED_COMPLETE`.
