# Bounded Task Contract

Optional collaboration uses contracts, not free-form agent conversation.

## Schema

```yaml
contract_id: combat-architecture
goal: Design the combat module boundary.
required_capabilities:
  - architecture
inputs:
  - GOAL.md
  - repository
allowed_actions:
  - inspect_repository
  - write_architecture_document
forbidden_actions:
  - modify_production_code
expected_outputs:
  - docs/combat-architecture.md
evidence_requirements:
  - output_file_exists
  - architecture_constraints_are_addressed
```

Every field is a boundary:

- `goal` states one observable result;
- `inputs` names the context supplied by the host;
- `allowed_actions` and `forbidden_actions` limit authority;
- `expected_outputs` defines return artifacts;
- `evidence_requirements` prevents unsupported completion claims.

An expert profile may be attached when its capabilities match. The profile is
metadata only and never creates an agent or grants permissions.

## Result

```yaml
contract_id: combat-architecture
status: COMPLETED
outputs:
  - docs/combat-architecture.md
evidence_refs:
  - evidence/architecture-review.txt
notes: []
```

`COMPLETED` requires both outputs and evidence. Results still return to the
shared Evidence Ledger, independent Judge, and Policy Gate.
