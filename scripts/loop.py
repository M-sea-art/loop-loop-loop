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
Use `.loop/GOALS.md` for subgoals and `.loop/REPORT.md` for the current worker report.
Run exactly one loop: Recover -> Discover -> Pick -> Execute -> Verify -> Report -> Accept -> Record.
Update `.loop/STATE.md` with status, evidence, blockers, and next_run_instruction.
Do not merge, publish, deploy, delete important files, reset history, use credentials, pay money, or claim formal completion.
"""

TEMPLATES = ["GOAL.md", "GOALS.md", "REPORT.md", "STATE.md", "CAPABILITIES.md", "EXPERIENCE.md", "ACCEPTANCE.md"]
SCORE_FIELDS = {
    "goal_completion": (25, ["goal_completion", "目标完成度"]),
    "usability": (20, ["usability", "可运行/可使用性", "可运行性", "可使用性"]),
    "quality": (20, ["quality", "结果质量"]),
    "ux_readability": (15, ["ux_readability", "用户体验/可读性", "用户体验", "可读性"]),
    "stability_correctness": (10, ["stability_correctness", "稳定性/正确性", "稳定性", "正确性"]),
    "delivery_completeness": (10, ["delivery_completeness", "交付完整度"]),
}
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


def schema_status(project: Path) -> tuple[bool, str]:
    schema = project / ".codex" / "runtime" / "loop_result.schema.json"
    try:
        data = json.loads(schema.read_text(encoding="utf-8"))
    except Exception as exc:
        return False, f"{type(exc).__name__}: {exc}"
    required = set(data.get("required", []))
    expected = {"status", "total_score", "scores", "actions_taken", "verification", "evidence", "acceptance", "blockers", "experience", "next_run_instruction"}
    missing = sorted(expected - required)
    return (not missing, f"missing required fields: {missing}" if missing else "")


def list_rel(project: Path, pattern: str) -> list[str]:
    return sorted(str(path.relative_to(project)) for path in project.glob(pattern) if path.is_file())


def capabilities(project: Path) -> dict[str, object]:
    return {
        "git": git_ok(project),
        "codex_cli": bool(shutil.which("codex")),
        "docs": list_rel(project, "README*") + list_rel(project, "AGENTS*"),
        "scripts": list_rel(project, "scripts/*"),
        "package_files": [
            name for name in ("package.json", "pyproject.toml", "Cargo.toml", "go.mod", "Makefile")
            if (project / name).exists()
        ],
        "project_skills": list_rel(project, ".codex/skills/*/SKILL.md"),
        "github_workflows": list_rel(project, ".github/workflows/*"),
    }


def check(project: Path) -> int:
    loop_dir = project / ".loop"
    runtime_dir = project / ".codex" / "runtime"
    missing_runtime = [name for name in RUNTIME_FILES if not (runtime_dir / name).exists()]
    missing_state = [name for name in TEMPLATES if not (loop_dir / name).exists()]
    schema_ok, schema_error = schema_status(project)
    result = {
        "runtime_ok": not missing_runtime,
        "missing_runtime": missing_runtime,
        "schema_ok": schema_ok,
        "schema_error": schema_error,
        "state_ok": not missing_state,
        "missing_state": missing_state,
        "codex_cli": bool(shutil.which("codex")),
        "git_repo": git_ok(project),
        "capabilities": capabilities(project),
        "secret_hits": scan_secrets(project),
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["runtime_ok"] and result["schema_ok"] and result["state_ok"] and not result["secret_hits"] else 1


def evidence_present(loop_dir: Path, combined: str) -> bool:
    if has_files(loop_dir / "evidence"):
        return True
    evidence_patterns = [
        r"(?im)^\s*-\s+.*(PASS|exit code:\s*0|test|build|log|screenshot|路径|证据)",
        r"(?im)^\s*(evidence|证据|验证|log|screenshot|report)\s*[:：]\s*(?!none|none yet|无|暂无).+",
        r"(?im)\b(PASS|exit code:\s*0|validated|verified)\b",
    ]
    return any(re.search(pattern, combined) for pattern in evidence_patterns)


def parse_scores(combined: str, has_evidence: bool) -> dict[str, float]:
    scores: dict[str, float] = {}
    any_explicit = False
    for key, (maxv, aliases) in SCORE_FIELDS.items():
        value: float | None = None
        for alias in aliases:
            patterns = [
                rf"(?im)^\s*{re.escape(alias)}\s*[:=]\s*(\d+(?:\.\d+)?)\s*$",
                rf"(?im)\|\s*{re.escape(alias)}\s*\|\s*{maxv}\s*\|\s*(\d+(?:\.\d+)?)\s*\|",
                rf"(?im)\|\s*{re.escape(alias)}\s*\|\s*(\d+(?:\.\d+)?)\s*/\s*{maxv}\s*\|",
            ]
            for pattern in patterns:
                match = re.search(pattern, combined)
                if match:
                    value = float(match.group(1))
                    break
            if value is not None:
                break
        if value is not None:
            any_explicit = True
            scores[key] = max(0, min(maxv, value))
        else:
            scores[key] = 0
    if not any_explicit and has_evidence:
        # ponytail: conservative floor for evidence without a real rubric; explicit scores replace this.
        scores = {
            "goal_completion": 10,
            "usability": 8,
            "quality": 8,
            "ux_readability": 6,
            "stability_correctness": 4,
            "delivery_completeness": 4,
        }
    return scores


def score_data(project: Path) -> dict[str, object]:
    loop_dir = project / ".loop"
    combined = "\n".join([text(loop_dir / name) for name in ("STATE.md", "REPORT.md", "ACCEPTANCE.md")])
    blocked = bool(re.search(r"(CANDIDATE_BLOCKED|blocked|阻塞|human gate|凭据|权限|验证码|付款)", combined, re.I))
    evidence = evidence_present(loop_dir, combined)
    scores = parse_scores(combined, evidence)
    total = sum(scores.values())
    pass_claim = "CANDIDATE_PASS" in combined
    status = "CANDIDATE_BLOCKED" if blocked else ("CANDIDATE_PASS" if pass_claim and evidence and total >= 95 else "CANDIDATE_PARTIAL")
    deductions = sorted(
        ({"field": key, "deduction": maxv - scores[key]} for key, (maxv, _) in SCORE_FIELDS.items()),
        key=lambda item: item["deduction"],
        reverse=True,
    )
    return {
        "status": status,
        "total_score": total,
        "scores": scores,
        "highest_deductions": deductions[:3],
        "has_evidence": evidence,
        "blocked": blocked,
        "next_run_instruction_present": "next_run_instruction" in combined,
    }


def score(project: Path) -> int:
    result = score_data(project)
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


def run_loop(project: Path, threshold: int, max_iterations: int) -> int:
    dry_run = os.environ.get("CODEX_DRY_RUN") == "1"
    iterations = 1 if dry_run else max_iterations
    last_score: dict[str, object] = {}
    for iteration in range(1, iterations + 1):
        print(f"loop iteration {iteration}/{iterations}")
        code = run(project)
        if code != 0:
            return code
        last_score = score_data(project)
        print(json.dumps(last_score, ensure_ascii=False, indent=2))
        if last_score["status"] == "CANDIDATE_BLOCKED":
            return 2
        if last_score["status"] == "CANDIDATE_PASS" and float(last_score["total_score"]) >= threshold:
            return 0
    if dry_run:
        return 0
    return 0 if last_score.get("status") == "CANDIDATE_PASS" else 2


def main() -> int:
    parser = argparse.ArgumentParser(description="loop loop loop runtime launcher")
    parser.add_argument("command", choices=["install", "init", "prompt", "check", "score", "run", "run-loop"])
    parser.add_argument("project", nargs="?", default=".")
    parser.add_argument("--threshold", type=int, default=95)
    parser.add_argument("--max-iterations", type=int, default=10)
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
    if args.command == "run-loop":
        return run_loop(project, args.threshold, args.max_iterations)
    return run(project)


if __name__ == "__main__":
    raise SystemExit(main())
