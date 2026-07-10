# Recovery Engine

Start from durable state, hashes, and repository reality rather than model memory.

Read in order:

1. `.loop/STATE.md`
2. `.loop/contract.lock.json`
3. `.loop/ACCEPTANCE_CONTRACT.json`
4. `.loop/EVIDENCE_LEDGER.jsonl`
5. `.loop/REVIEW.md`
6. `.loop/ACCEPTANCE.md`

If the contract hash, policy hash, evidence artifact hash, workspace fingerprint, or review receipt is stale, invalidate the dependent decision. Do not preserve a PASS across changed evidence or artifacts.
