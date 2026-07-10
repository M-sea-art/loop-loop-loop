---
name: loop-loop-loop
description: Run an evidence-gated Codex loop with a frozen acceptance contract, direct artifact evidence, independent read-only review, adversarial challenge, and deterministic promotion policy.
---

# loop loop loop Skill

Use this when the user asks to keep looping, run until done, improve autonomously, or use the Codex Loop Runtime.

Procedure:

1. Read `.codex/runtime/INDEX.md`.
2. Recover `.loop/STATE.md`, the contract lock, evidence ledger, and latest independent review.
3. Frame and freeze acceptance before implementation when no valid contract exists.
4. Run one worker loop only.
5. Record direct outcome/scenario evidence.
6. Run a fresh read-only independent review and challenge when evidence coverage is complete.
7. Let `python scripts/loop.py gate .` determine promotion.
8. If not independently verified, write the smallest evidence-backed next instruction.

The worker cannot approve itself. Scores and process metrics cannot produce PASS.
