#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path


PROMPT = """Start Runtime.

Read `.codex/runtime/INDEX.md`.
Recover `.loop/STATE.md` and `.loop/GOAL.md`.
Run exactly one loop: Recover -> Discover -> Pick -> Execute -> Verify -> Accept -> Record.
Update `.loop/STATE.md` with status, evidence, blockers, and next_run_instruction.
Do not merge, publish, deploy, delete important files, reset history, use credentials, pay money, or claim formal completion.
"""

TEMPLATES = ["GOAL.md", "STATE.md", "CAPABILITIES.md", "EXPERIENCE.md", "ACCEPTANCE.md"]
RUNTIME_FILES = [
    "INDEX.md",
    "orchestrator.md",
    "recovery.md",
    "capability.md",
    "agent-factory.md",
    "verification.md",
    "acceptance.md",
    "experience.md",
    "loop_result.schema.json",
]
SECRET_RE = re.compile(
    r"(gho_[A-Za-z0-9_]+|sk-[A-Za-z0-9_-]{20,}|BEGIN (RSA|OPENSSH|PRIVATE) KEY|(?:api[_-]?key|secret|token|password|passwd)\s*[:=]\s*['\"]?[A-Za-z0-9_./+=-]{16,})",
    re.I,
)


def root(path: str) -> Path:
    return Path(path).resolve()


def kit_root() -> Path:
    return Path(__file__).resolve().parents[1]


def copy_dir(src: Path, dest: Path) -> None:
    if src.resolve() == dest.resolve():
        return
    shutil.copytree(src, dest, dirs_exist_ok=True)


def copy_file(src: Path, dest: Path) -> None:
    if src.resolve() == dest.resolve():
        return
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dest)


def install(project: Path) -> None:
    kit = kit_root()
    copy_dir(kit / ".codex" / "runtime", project / ".codex" / "runtime")
    copy_dir(kit / ".codex" / "skills" / "loop-loop-loop", project / ".codex" / "skills" / "loop-loop-loop")
    copy_dir(kit / "templates", project / "templates")
    for name in ("loop.py", "loop_once.sh", "loop_once.ps1"):
        copy_file(kit / "scripts" / name, project / "scripts" / name)
    init(project)
    print(f"installed loop loop loop runtime into {project}")


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


def has_files(path: Path) -> bool:
    return path.exists() and any(p.is_file() for p in path.rglob("*"))


def text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore") if path.exists() else ""


def scan_secrets(project: Path) -> list[str]:
    hits: list[str] = []
    for path in project.rglob("*"):
        if (
            not path.is_file()
            or ".git" in path.parts
            or "__pycache__" in path.parts
            or path.stat().st_size > 500_000
        ):
            continue
        try:
            for i, line in enumerate(path.read_text(encoding="utf-8", errors="ignore").splitlines(), 1):
                if SECRET_RE.search(line):
                    hits.append(f"{path.relative_to(project)}:{i}")
        except OSError:
            continue
    return hits


def git_ok(project: Path) -> bool:
    result = subprocess.run(["git", "rev-parse", "--is-inside-work-tree"], cwd=project, capture_output=True, text=True)
    return result.returncode == 0 and result.stdout.strip() == "true"


def check(project: Path) -> int:
    loop_dir = project / ".loop"
    runtime_dir = project / ".codex" / "runtime"
    missing_runtime = [name for name in RUNTIME_FILES if not (runtime_dir / name).exists()]
    missing_state = [name for name in TEMPLATES if not (loop_dir / name).exists()]
    result = {
        "runtime_ok": not missing_runtime,
        "missing_runtime": missing_runtime,
        "state_ok": not missing_state,
        "missing_state": missing_state,
        "codex_cli": bool(shutil.which("codex")),
        "git_repo": git_ok(project),
        "secret_hits": scan_secrets(project),
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["runtime_ok"] and result["state_ok"] and not result["secret_hits"] else 1


def score(project: Path) -> int:
    loop_dir = project / ".loop"
    combined = "\n".join([text(loop_dir / "STATE.md"), text(loop_dir / "ACCEPTANCE.md")])
    blocked = bool(re.search(r"(CANDIDATE_BLOCKED|blocked|阻塞|human gate|凭据|权限|验证码|付款)", combined, re.I))
    evidence = has_files(loop_dir / "evidence") or bool(re.search(r"(evidence|证据|验证|test|build|log|screenshot)", combined, re.I))
    pass_claim = "CANDIDATE_PASS" in combined
    status = "CANDIDATE_BLOCKED" if blocked else ("CANDIDATE_PASS" if pass_claim and evidence else "CANDIDATE_PARTIAL")
    result = {
        "status": status,
        "has_evidence": evidence,
        "blocked": blocked,
        "next_run_instruction_present": "next_run_instruction" in combined,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


def run(project: Path) -> int:
    init(project)
    if os.environ.get("CODEX_DRY_RUN") == "1":
        prompt()
        return 0

    sandbox = os.environ.get("CODEX_SANDBOX", "workspace-write")
    report = project / ".loop" / "reports" / f"loop-{datetime.now().strftime('%Y%m%d-%H%M%S')}.md"
    schema = project / ".codex" / "runtime" / "loop_result.schema.json"
    cmd = ["codex", "exec", "--sandbox", sandbox, "--output-schema", str(schema), "-o", str(report), "-"]
    try:
        return subprocess.run(cmd, input=PROMPT, text=True, cwd=project).returncode
    except FileNotFoundError:
        print("codex CLI not found. Set CODEX_DRY_RUN=1 to inspect the startup prompt.", file=sys.stderr)
        return 127


def main() -> int:
    parser = argparse.ArgumentParser(description="loop loop loop runtime launcher")
    parser.add_argument("command", choices=["install", "init", "prompt", "check", "score", "run"])
    parser.add_argument("project", nargs="?", default=".")
    args = parser.parse_args()

    project = root(args.project)
    if args.command == "install":
        install(project)
        return 0
    if args.command == "init":
        init(project)
        return 0
    if args.command == "prompt":
        prompt()
        return 0
    if args.command == "check":
        return check(project)
    if args.command == "score":
        return score(project)
    return run(project)


if __name__ == "__main__":
    raise SystemExit(main())
