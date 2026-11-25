# Complexity Routing

The complexity analyzer recommends an execution shape. The mode policy applies
authorization separately.

## Inputs

- affected files;
- affected modules;
- domain count;
- risk level;
- parallel work items;
- specialist capability count.

These signals are explicit goal-framing data. The analyzer does not inspect
Codex configuration or infer permission from available tools.

## Deterministic scoring

| Signal | Score |
| --- | ---: |
| Multiple files | +1 |
| Multiple modules | +1 |
| Multiple domains | +2 |
| Medium risk | +1 |
| High risk | +2 |
| 2–3 parallel work items | +1 |
| 4+ parallel work items | +2 |
| Multiple specialist capabilities | +1 |

Recommendation:

- 0–1: `single`;
- 2–5: `assisted`;
- 6+: `swarm`.

The thresholds are transparent policy, not learned authorization.

## Decision example

```json
{
  "recommended_mode": "swarm",
  "authorized_ceiling": "single",
  "selected_mode": "single",
  "authorization_source": "default_single",
  "reasons": ["multiple_domains", "high_risk", "strong_parallel_opportunity"],
  "needs_additional_authorization": true,
  "codex_settings_preserved": true
}
```

The runtime may de-escalate within the authorized range. It cannot escalate
beyond that range.
