# Adaptive Execution v2 Phase 4: Bounded Delegation

## Purpose

Bounded Delegation adds controlled task delegation on top of Runtime Reliability.

Delegation improves execution efficiency, but it must never become a replacement for authority, evidence, or verification.

## Core Rule

```
More workers != more authority
```

A delegated worker receives only the minimum capability required for its assigned scope.

## Delegation Flow

```
Goal
 ↓
Orchestration Plan
 ↓
Scoped Delegation
 ↓
Child Result Contract
 ↓
Integration Writer
 ↓
Evidence
 ↓
Judge
 ↓
Gate
```

## Task Scope

Every delegated task must define:

- task_id
- goal_id
- allowed_scope
- forbidden_actions
- expected_result
- evidence_requirements
- expiration

## Permission Rules

Delegated workers:

- cannot modify authority state directly;
- cannot bypass leases;
- cannot declare goal completion;
- cannot replace the integration writer.

## Result Contract

A child result is an input, not a final truth.

```
Child Result
     ↓
Integration
     ↓
Evidence
     ↓
Judge
     ↓
Terminal State
```

## Safety Properties

Bounded Delegation preserves Runtime Reliability:

- authority remains centralized;
- evidence remains mandatory;
- review remains independent;
- delegation can be revoked;
- failed delegation does not corrupt goal state.
