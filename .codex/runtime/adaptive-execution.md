# Adaptive Execution

LoopLoopLoop adapts to the Codex runtime that is already active. It does not
replace Codex orchestration, permissions, configuration, or approval gates.

## Default

Use the current Codex agent and run the normal loop. Complexity assessment may
recommend collaboration, but a recommendation is not authorization.

## Authorization ceiling

Collaboration may expand only when the current user request or a user-approved
project policy explicitly permits it:

- `single`: current agent only;
- `assisted`: current agent plus one bounded specialist collaboration;
- `swarm`: multiple bounded work contracts through Codex-native delegation.

The selected mode is the lower of the recommended mode and the authorized
ceiling. An explicit `force_single` instruction wins over every recommendation.

## Codex compatibility boundary

- Use only delegation capabilities exposed by the active Codex host.
- Preserve Codex defaults for models, permissions, sandboxing, approvals,
  concurrency, context management, and tool access.
- Do not create or modify global Codex configuration.
- Do not install or run a parallel agent framework, background coordinator, or
  custom permission system.
- If native delegation is unavailable, continue sequentially with the current
  agent instead of emulating a swarm.
- Never let collaboration bypass evidence, independent review, challenge, or
  the configured runtime gate. If a project constitution explicitly replaces
  a legacy human gate with autonomous evidence review, preserve that contract
  exactly rather than reintroducing a waiting state.

Expert profiles are capability metadata. They do not create agents. Every
delegated unit must receive a bounded task contract, return evidence, and feed
the same final Judge and Policy Gate.
