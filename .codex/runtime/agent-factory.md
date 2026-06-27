# Agent Factory

Agents are temporary roles created from capability gaps.

Create a role only when it changes the result:

- builder: makes the change
- verifier: rejects without evidence
- researcher: resolves a missing fact
- reviewer: checks risk or UX
- integrator: connects already-built parts

The maker cannot approve its own work.

If real subagents are unavailable, simulate roles in the same run and record that in `.loop/STATE.md`.

