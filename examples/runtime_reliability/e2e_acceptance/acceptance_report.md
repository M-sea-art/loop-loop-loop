# Runtime Reliability v1 Acceptance Report

## Purpose

This document defines the expected final evidence for Runtime Reliability v1.

## Required Scenarios

### Successful Goal

Expected terminal state:

`VERIFIED_COMPLETE`

Requirements:

- goal contract satisfied
- evidence recorded
- judge verification passed

### Revoked Goal

Expected terminal state:

`VERIFIED_STOPPED`

Requirements:

- revoke event recorded
- future mutation denied

### No Progress

Expected terminal state:

`STOPPED_NO_PROGRESS`

Requirements:

- activity alone does not count as progress
- repeated no-op cycles stop execution

### Writer Conflict

Expected result:

`SECOND_WRITER_REJECTED`

Requirements:

- one goal has one active writer
- conflicting mutation is denied
