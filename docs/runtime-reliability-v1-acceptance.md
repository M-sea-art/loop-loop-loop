# Runtime Reliability v1 Acceptance

## Goal

Verify that LoopLoopLoop can distinguish real completion from activity.

## Required scenarios

- success_case: a goal reaches verified completion.
- revoke_case: a stopped goal cannot silently resume.
- no_progress_case: repeated activity without progress triggers stop-loss.
- writer_conflict_case: competing writers are rejected.

## Acceptance principle

A running loop is not proof of progress.
A created artifact is not proof of success.
Only evidence-backed verification can produce a completed state.
