# Adaptive Execution v2 Phase 3: Orchestration Plan

## Purpose

Orchestration Plan is a planning layer, not an execution authority.

It describes how a goal may be executed after complexity assessment, while Reliability Runtime remains the only authority for state, evidence, and completion.

## Flow

Goal

↓

Complexity Assessment

↓

Orchestration Plan

↓

Authorized Execution Mode

↓

Reliability Runtime

## Plan Schema

Example:

```json
{
  "goal_id": "G001",
  "recommended_mode": "assisted",
  "participants": [
    {
      "role": "researcher",
      "permission": "read_only"
    },
    {
      "role": "reviewer",
      "permission": "read_only"
    }
  ],
  "constraints": [
    "single_writer",
    "evidence_required",
    "judge_required"
  ]
}
```

## Rules

- Plan does not grant permission.
- Participants do not gain authority automatically.
- Child results cannot directly complete a goal.
- Final integration must pass through Reliability Runtime.
- Authority Event, Evidence, Judge, and Gate remain mandatory.

## Goal

Increase execution flexibility without weakening correctness guarantees.
