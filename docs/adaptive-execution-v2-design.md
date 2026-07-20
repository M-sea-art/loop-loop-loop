# LoopLoopLoop Adaptive Execution v2 Design

## Purpose

Adaptive Execution is an extension layer above Runtime Reliability.

It does not replace Goal, Authority, Evidence, Judge, or Gate.

The Runtime decides correctness. Adaptive Execution only decides how to organize execution.

## Core Principle

More agents do not automatically mean more progress.

The system must first determine:

- Is parallel work useful?
- Is additional coordination worth the cost?
- Can the current writer complete the goal safely?

## Execution Modes

### Single

Default mode.

One goal, one active writer, one reliability lifecycle.

### Assisted

Limited collaboration.

Example:

- Writer: mutation authority
- Researcher: read-only
- Reviewer: read-only

Supporting roles cannot modify authoritative state.

### Swarm

Advanced mode.

Multiple workers may explore bounded tasks, but integration must return to a single controlled writer before acceptance.

## Complexity Assessment

Adaptive routing begins with recommendation, not automatic expansion.

Input:

- goal size
- dependency count
- uncertainty
- parallel opportunity
- risk

Output:

- recommended mode
- confidence
- explanation

## Permission Model

Complexity does not grant permission.

Capabilities are explicit:

Role -> Capability -> Permission

Observer and reviewer roles remain read-only.

## Safety Constraints

Adaptive Execution must never:

- bypass Authority Event Log
- bypass Evidence verification
- create unlimited workers automatically
- allow child workers to declare Goal completion
- modify Codex permissions or sandbox settings

## Roadmap

Phase 1: Complexity Assessment

Phase 2: Execution Mode Contracts

Phase 3: Orchestration Plan

Phase 4: Bounded Native Delegation

Phase 5: Multi-worker integration after reliability validation
