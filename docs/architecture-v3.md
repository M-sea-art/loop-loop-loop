# LoopLoopLoop Architecture v3

## Product boundary

LoopLoopLoop remains responsible for verified goal completion. Codex remains
responsible for its execution environment.

```text
Human Intent
    |
Goal Architect
    |
Complexity Recommendation ---- User Authorization Ceiling
    |                                      |
    +-------------- Mode Policy -----------+
                           |
             single / assisted / swarm
                           |
              Codex-native execution
                           |
              Shared Evidence Ledger
                           |
                 Independent Judge
                           |
                    Policy Gate
```

The mode branch changes how bounded execution work may be distributed. Every
branch converges before evidence and acceptance.

## Components

| Component | Responsibility | Authority |
| --- | --- | --- |
| Complexity Analyzer | Recommend a mode from explicit signals | Advisory only |
| Mode Policy | Cap recommendation by authorization | Cannot change Codex settings |
| Expert Registry | Match capability metadata | Cannot create agents |
| Adaptive Orchestrator | Prepare bounded contracts | Cannot grant permission or approve results |
| Codex Host | Execute using native capabilities | Existing Codex boundaries |
| Evidence/Judge/Gate | Verify and promote outcomes | Existing completion contract |

## Compatibility guarantees

1. `LoopRuntime.run_once()` preserves the v2 lifecycle.
2. Adaptive execution is exposed through `LoopRuntime.prepare_execution()`.
3. Default authorization selects `single`, even when complexity recommends
   `assisted` or `swarm`.
4. No module reads or writes global Codex settings.
5. Optional collaboration cannot approve its own work.

## Integration boundaries

- `gpt-pro-review-loop` may supply an optional review adapter.
- `codex-efficiency-auditor` may supply capability discovery metadata.
- Neither is a required core dependency.

## Delivery stages

- v2.1: complexity assessment, authorization gate, expert registry;
- v2.2: bounded task/result contracts and Codex-native orchestration plans;
- v2.3: dependency graphs and shared evidence for native parallel execution;
- v2.4: adaptive mode changes within a previously authorized ceiling.
