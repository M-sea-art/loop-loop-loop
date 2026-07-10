# Verification Engine

No direct evidence, no promotion.

Verification must bind every required outcome/scenario pair to an artifact and an observation method that would fail if the outcome were false. Record evidence through `scripts/loop.py record-evidence` so artifact hashes and contract hashes are captured.

Build, lint, console cleanliness, test count, screenshot count, and score are supporting signals only. They cannot substitute for actual runtime, render, recomputation, document, end-to-end, or source evidence.

Never delete, disable, weaken, or reinterpret a failing rule to pass. A rule correction requires separate change control and must retain a regression case for the original failure.
