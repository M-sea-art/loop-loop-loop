# Agent Factory

Roles are temporary capabilities with explicit permissions.

- framer: reads goal and project, writes only a candidate acceptance contract
- worker: changes implementation and records direct evidence
- verifier: runs deterministic checks but cannot approve
- independent reviewer: fresh process, read-only, challenges final artifacts
- policy gate: deterministic state promotion from hashes and evidence

The maker cannot approve its own work. Simulated roles inside the same context may help diagnosis, but they are not independent and cannot satisfy the independent-review gate.
