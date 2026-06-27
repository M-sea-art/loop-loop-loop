# Verification Engine

No evidence, no pass.

Verification should be the smallest check that would fail if the change is wrong:

- unit test, smoke test, build, lint, dry run, screenshot, log, or manual command
- exact command and exit status
- evidence path under `.loop/evidence/` when useful

If no runnable check exists, create the smallest practical check or mark `needs_evidence`.

Never delete, disable, or weaken failing checks to pass.

Each score field must cite evidence. Unbound score fields are capped by the local scorer and cannot carry a candidate to pass.

Default local checks:

```bash
python scripts/loop.py check .
python scripts/loop.py score .
```
