#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path


PROMPT = """Start Runtime.

Read `.codex/runtime/INDEX.md`.
Recover `.loop/STATE.md` and `.loop/GOAL.md`.
Run exactly one loop: Recover -> Discover -> Pick -> Execute -> Verify -> Accept -> Record.
Update `.loop/STATE.md` with status, evidence, blockers, and next_run_instruction.
Do not merge, publish, deploy, delete important files, reset history, use credentials, pay money, or claim formal completion.
"""

TEMPLATES = ["GOAL.md", "STATE.md", "CAPABILITIES.md", "EXPERIENCE.md", "ACCEPTANCE.md"]


def root(path: str) -> Path:
    return Path(path).resolve()


def init(project: Path) -> None:
    loop_dir = project / ".loop"
    loop_dir.mkdir(exist_ok=True)
    (loop_dir / "reports").mkdir(exist_ok=True)
    (loop_dir / "evidence").mkdir(exist_ok=True)

    template_dir = project / "templates"
    for name in TEMPLATES:
        target = loop_dir / name
        if not target.exists():
            target.write_text((template_dir / name).read_text(encoding="utf-8"), encoding="utf-8")

    print(f"initialized {loop_dir}")


def prompt() -> None:
    print(PROMPT)


def run(project: Path) -> int:
    init(project)
    if os.environ.get("CODEX_DRY_RUN") == "1":
        prompt()
        return 0

    sandbox = os.environ.get("CODEX_SANDBOX", "workspace-write")
    cmd = ["codex", "exec", "--sandbox", sandbox, "-"]
    try:
        return subprocess.run(cmd, input=PROMPT, text=True, cwd=project).returncode
    except FileNotFoundError:
        print("codex CLI not found. Set CODEX_DRY_RUN=1 to inspect the startup prompt.", file=sys.stderr)
        return 127


def main() -> int:
    parser = argparse.ArgumentParser(description="loop loop loop runtime launcher")
    parser.add_argument("command", choices=["init", "prompt", "run"])
    parser.add_argument("project", nargs="?", default=".")
    args = parser.parse_args()

    project = root(args.project)
    if args.command == "init":
        init(project)
        return 0
    if args.command == "prompt":
        prompt()
        return 0
    return run(project)


if __name__ == "__main__":
    raise SystemExit(main())

