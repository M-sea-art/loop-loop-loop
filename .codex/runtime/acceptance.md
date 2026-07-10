# Acceptance Engine

Acceptance is a deterministic policy gate, not a worker opinion.

A candidate can reach `INDEPENDENTLY_VERIFIED` only when:

1. the contract and policy hashes remain frozen;
2. every required outcome/scenario pair has valid direct evidence;
3. evidence artifacts still exist and match their hashes;
4. a separate read-only reviewer evaluated the same workspace and evidence hashes;
5. every required claim passed independent review;
6. no P0/P1 finding remains;
7. challenge passed for every artifact modality;
8. no risk-based human gate remains.

Scores are diagnostic only. A worker cannot emit `CANDIDATE_PASS`. Contract drift, policy drift, stale review, or changed evidence invalidates prior acceptance.
