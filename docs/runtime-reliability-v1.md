# Runtime Reliability v1

## Purpose

LoopLoopLoop should evolve from a verified goal-completion prototype into a reliable goal-completion runtime.

The next priority is not increasing execution scale or adding more agents. The priority is ensuring the runtime can determine:

- who is allowed to write;
- whether real progress happened;
- whether state is trustworthy;
- when execution must stop.

## Core Principle

Activity is not progress.

Valid progress requires at least one of:

- a verifiable business artifact change;
- increased acceptance coverage;
- a real blocker being removed;
- a gate-verified terminal state.

The following are not progress:

- rewriting status projections;
- generating duplicate receipts;
- changing thread or agent counts;
- heartbeat activity;
- repeated completion claims.

## Runtime Reliability Model

```text
Authority Event Log
        |
        v
Deterministic State Projection
        |
        +----------------+
        |                |
        v                v
     Planner           Judge
        |                |
        v                v
     Executor -----> Evidence
        |
        v
      Gate
```

## Single Writer Rule

Default runtime contract:

```
one project
  -> one active goal
  -> one active writer
  -> one auditable lease
```

Observers, reviewers, patrol processes, and reporting layers must not mutate authoritative state.

## Terminal States

The runtime should support explicit outcomes:

- VERIFIED_COMPLETE
- VERIFIED_STOPPED
- WAIT_AUTHORITY
- STOPPED_NO_PROGRESS
- RECONCILE_REQUIRED
- FAILED_TERMINAL

Stopping correctly is a valid runtime result.

## Relationship With Adaptive Execution

Adaptive execution remains valuable, but only after runtime reliability guarantees exist.

The sequence is:

1. Reliable state and authority.
2. Reality-aware verification.
3. Evidence hardening.
4. Adaptive execution.

More agents cannot compensate for unreliable state.
