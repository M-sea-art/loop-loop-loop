# Runtime Reliability v1 Integration

The runtime flow is:

```text
Goal
 ↓
Executor
 ↓
Mutation Boundary
 ↓
Lease / Revocation Check
 ↓
Authority Event
 ↓
Projection
 ↓
Evidence
 ↓
Judge
 ↓
Gate
```

The purpose is not to increase execution complexity. The purpose is to ensure
that execution cannot bypass reality checks.

## Invariants

- No valid writer lease means no mutation.
- Revoked goals cannot resume automatically.
- Activity signals are not progress evidence.
- Terminal states must be explicit.
