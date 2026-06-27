# loop loop loop

**It doesn't stop until it's done.**

`loop loop loop` is a tiny Codex Loop Runtime. It is not a long prompt repo.

The prompt starts the runtime. The runtime owns the loop.

```text
Prompt -> Runtime -> State -> Capability -> Verify -> Experience -> Repeat
```

## What It Is

- a short startup prompt
- a file-backed runtime under `.codex/runtime/`
- persistent state under `.loop/`
- a local launcher in `scripts/loop.py`
- a place for capabilities and experience to become reusable skills

## Quick Start

```bash
git clone https://github.com/M-sea-art/loop-loop-loop.git
cd loop-loop-loop
python scripts/loop.py install C:\path\to\your\project
python scripts/loop.py check C:\path\to\your\project
python scripts/loop.py run C:\path\to\your\project
```

Inside this repository:

```bash
python scripts/loop.py init
python scripts/loop.py prompt
python scripts/loop.py check
```

Run one Codex loop:

```bash
python scripts/loop.py run
```

Dry-run through the shell wrapper:

```bash
CODEX_DRY_RUN=1 bash scripts/loop_once.sh .
```

## Runtime Shape

```text
.codex/runtime/
  INDEX.md
  orchestrator.md
  capability.md
  agent-factory.md
  verification.md
  acceptance.md
  experience.md
  recovery.md

.loop/
  GOAL.md
  STATE.md
  CAPABILITIES.md
  EXPERIENCE.md
  ACCEPTANCE.md
  reports/
  evidence/
```

The runtime keeps the prompt small:

```text
Start Runtime.
Read .codex/runtime/INDEX.md.
Recover .loop/STATE.md.
Continue one loop.
```

## Loop Contract

Each run does one high-value loop:

```text
Recover -> Discover -> Pick -> Execute -> Verify -> Accept -> Record
```

It stops only with one of:

- `CANDIDATE_PASS`
- `CANDIDATE_PARTIAL` with a written `next_run_instruction`
- `CANDIDATE_BLOCKED` with the smallest unblock step
- a human gate such as credentials, payment, production deploy, destructive reset, or formal approval

## Design Bias

Prompt gets shorter.
Runtime gets stronger.
Experience becomes skill.

## Commands

- `install <project>` copies the runtime, project skill, templates, and launcher scripts into a project.
- `init <project>` creates `.loop/` state without overwriting existing state.
- `prompt` prints the short startup prompt.
- `check <project>` checks runtime files, state files, Codex CLI, Git, and obvious secret patterns.
- `score <project>` applies the minimum no-evidence-no-pass rule.
- `run <project>` runs one `codex exec` loop with the result schema and writes `.loop/reports/`.
