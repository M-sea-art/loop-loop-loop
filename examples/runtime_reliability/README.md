# Runtime Reliability Examples

These executable acceptance scenarios prove that LoopLoopLoop distinguishes
verified goal completion from activity.

Run all scenarios:

```bash
python examples/runtime_reliability/run_all_scenarios.py
```

Expected outcomes:

| Scenario | Expected outcome |
| --- | --- |
| successful goal | `VERIFIED_COMPLETE` |
| human revoke | `VERIFIED_STOPPED` |
| repeated activity without evidence | `STOPPED_NO_PROGRESS` |
| concurrent writers | `SECOND_WRITER_REJECTED` |

The production `LoopRuntime` path passes through the same reliability boundary.
A goal contract is frozen before execution, the writer mutates only under a
lease, authority events are signed, and completion requires a separate reviewer
capability bound to the frozen contract.

Run the full regression suite with only the Python standard library:

```bash
python -W error -m unittest discover -s tests -v
```
