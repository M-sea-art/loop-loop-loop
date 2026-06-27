# Experience Engine

Experience becomes future runtime behavior.

After each loop, append to `.loop/EXPERIENCE.md`:

- what worked
- what failed
- reusable command, skill, tool, or pattern
- capability gap discovered
- whether the lesson should become a skill

Only promote repeated lessons to skills. One-off notes stay in experience.

v0 appends experience only. It does not write global skills automatically.

Use `python scripts/loop.py distill-experience .` to write reviewed candidate skills under `.loop/skill-candidates/`. Promotion to global skills remains a human decision.
