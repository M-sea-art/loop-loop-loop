# Acceptance Contract

Compile the user's goal into `.loop/ACCEPTANCE_CONTRACT.json` before implementation.

The contract must define:

- user intent as an observable outcome
- required artifact modalities
- outcome IDs and scenario coverage
- direct evidence types for each outcome
- prohibited failures
- process proxies that cannot prove completion
- automation, independent-review, challenge, human-review, and risk gates

`freeze-contract` writes `.loop/contract.lock.json` with contract, goal, and policy hashes. After freezing, the worker must not change the contract or policy. Drift invalidates review and acceptance. A legitimate change requires an explicit change-control cycle, not a silent re-freeze.
