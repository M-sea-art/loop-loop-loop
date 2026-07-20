# Adaptive Execution v2 Phase 1: Complexity Assessment

## Purpose

Adaptive Execution must decide whether a goal needs additional coordination without weakening Runtime Reliability guarantees.

Complexity assessment is only a recommendation layer.

It does not grant permissions, create agents, or bypass authority controls.

## Principles

- Complexity does not equal permission.
- More agents do not automatically mean better results.
- Single writer remains the default.
- Reliability Runtime remains the source of truth.

## Assessment Inputs

- goal size
- dependency count
- uncertainty
- parallelization potential
- verification difficulty
- risk level

## Output

Example:

```json
{
  "recommended_mode": "single",
  "confidence": 0.9,
  "reason": "Task has low dependency and limited uncertainty"
}
```

## Execution Modes

### Single

Default mode:

- one active writer
- one goal lifecycle
- normal Reliability Runtime path

### Assisted

Limited collaboration:

- additional read-only roles may help
- integration remains single writer

### Swarm

Advanced mode:

- requires explicit authorization
- child results must return through integration writer
- cannot directly complete a goal

## Boundary

Adaptive Execution improves coordination.

Reliability Runtime decides truth.
