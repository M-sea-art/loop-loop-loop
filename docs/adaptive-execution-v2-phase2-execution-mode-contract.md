# Adaptive Execution v2 Phase 2 - Execution Mode Contract

## Purpose

Define bounded execution modes above Runtime Reliability v1.

Adaptive Execution changes execution strategy, not authority.

The Reliability Runtime remains the source of truth for:

- goal state
- authority events
- evidence
- judgement
- terminal states

## Execution Modes

### Single

Default mode.

Properties:

- one goal
- one active writer
- one lifecycle
- full Reliability Runtime protection

### Assisted

Limited collaboration mode.

Allowed:

- read-only research
- read-only review
- bounded helper tasks

Rules:

- one integration writer remains responsible for mutations
- helper output is evidence/input, not completion proof

### Swarm

Advanced parallel execution mode.

Rules:

- requires explicit authorization
- child workers cannot complete goals directly
- child results must return through integration writer
- final result requires evidence and gate validation

## Permission Boundary

Complexity does not grant permission.

Role -> Capability -> Permission

Execution mode only affects coordination. It does not bypass:

- authority event log
- writer lease
- evidence verification
- judge gate

## Non Goals

This phase does not implement:

- automatic unlimited agent spawning
- permission escalation
- Codex configuration changes
- replacement of native delegation
