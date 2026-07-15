# Optional Collaboration Modes

LoopLoopLoop is an adaptive goal-completion runtime, not a replacement for the
Codex agent runtime.

## Invariant

The normal path uses the current Codex agent:

```text
Goal -> Planner -> Executor -> Evidence -> Judge -> Gate
```

Execution collaboration is an upper-layer option. It does not alter the goal
contract, evidence model, Judge, Policy Gate, Codex permissions, or Codex
configuration.

## Modes

| Mode | Execution shape | Authorization |
| --- | --- | --- |
| `single` | Current Codex agent executes sequentially | Default |
| `assisted` | Current agent plus one bounded specialist collaboration | Explicit user ceiling |
| `swarm` | Multiple bounded work contracts through native Codex delegation | Explicit user ceiling |

Independent verification is part of the existing completion gate. It is not a
license to create an execution swarm.

## Selection rule

```text
selected mode = recommendation capped by user authorization
```

Complexity may recommend a higher mode. Without authorization, the selected
mode remains `single`. An explicit `force_single` instruction always wins.

Authorization may come from the current user request or a user-approved project
policy. A model inference, task score, or expert profile is never authorization.

## Codex-native boundary

LoopLoopLoop prepares routing decisions and bounded contracts. The active Codex
host owns actual delegation, concurrency, context, models, tools, sandboxing,
permissions, and approvals.

The runtime must not:

- write global Codex configuration;
- change Codex permission or approval settings;
- start an external multi-agent framework;
- pretend sequential role-play is independent execution;
- bypass evidence, independent review, challenge, or the configured runtime gate. A project constitution may explicitly replace a legacy human gate with autonomous evidence review; collaboration does not weaken or reinterpret that contract.

If native delegation is unavailable, work continues sequentially with the
current agent.
