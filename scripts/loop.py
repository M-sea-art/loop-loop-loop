#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


TEMPLATES = [
    "GOAL.md",
    "GOALS.md",
    "REPORT.md",
    "SEARCH_PLAN.md",
    "REUSE_CANDIDATES.md",
    "AUTOMATION_HANDOFF.md",
    "STATE.md",
    "CAPABILITIES.md",
    "EXPERIENCE.md",
    "ACCEPTANCE.md",
    "ACCEPTANCE_CONTRACT.json",
    "PLAN.md",
    "EVIDENCE.md",
    "EVIDENCE_LEDGER.jsonl",
    "REVIEW.md",
    "FAILURE_PATTERNS.md",
]

RUNTIME_FILES = [
    "INDEX.md",
    "orchestrator.md",
    "recovery.md",
    "adaptive-execution.md",
    "capability.md",
    "agent-factory.md",
    "contract.md",
    "verification.md",
    "observation.md",
    "challenge.md",
    "acceptance.md",
    "experience.md",
    "loop_result.schema.json",
    "acceptance_contract.schema.json",
    "review_result.schema.json",
]

POLICY_FILES = [
    ".codex/runtime/adaptive-execution.md",
    ".codex/runtime/contract.md",
    ".codex/runtime/verification.md",
    ".codex/runtime/observation.md",
    ".codex/runtime/challenge.md",
    ".codex/runtime/acceptance.md",
    ".codex/runtime/acceptance_contract.schema.json",
    ".codex/runtime/review_result.schema.json",
    "scripts/loop.py",
]

SCORE_FIELDS = {
    "goal_completion": (25, ["goal_completion", "目标完成度"]),
    "usability": (20, ["usability", "可运行/可使用性", "可运行性", "可使用性"]),
    "quality": (20, ["quality", "结果质量"]),
    "ux_readability": (15, ["ux_readability", "用户体验/可读性", "用户体验", "可读性"]),
    "stability_correctness": (10, ["stability_correctness", "稳定性/正确性", "稳定性", "正确性"]),
    "delivery_completeness": (10, ["delivery_completeness", "交付完整度"]),
}

ALLOWED_MODALITIES = {"general", "code", "visual", "data", "document", "automation", "research"}
MODALITY_EVIDENCE = {
    "general": {"inspection", "test", "runtime"},
    "code": {"test", "runtime", "integration_test", "property_test"},
    "visual": {"screenshot", "render", "visual_review", "browser_observation"},
    "data": {"recompute", "data_assertion", "fixture", "cross_check"},
    "document": {"document_render", "pdf_render", "page_inspection"},
    "automation": {"end_to_end", "state_assertion", "replay"},
    "research": {"source_crosscheck", "citation", "primary_source"},
}

PLACEHOLDER_RE = re.compile(
    r"(describe the|replace with|none yet|pending|todo|tbd|define the first|candidate outcome|real operating state)",
    re.I,
)
SECRET_RE = re.compile(
    r"(gho_[A-Za-z0-9_]+|sk-[A-Za-z0-9_-]{20,}|BEGIN (RSA|OPENSSH|PRIVATE) KEY|(?:api[_-]?key|secret|token|password|passwd)\s*[:=]\s*['\"]?[A-Za-z0-9_./+=-]{16,})",
    re.I,
)

VOLATILE_PREFIXES = (
    ".git/",
    ".loop/reports/",
    ".loop/reviews/",
    ".loop/tmp/",
    ".loop/evidence/",
    "__pycache__/",
)
VOLATILE_FILES = {
    ".loop/STATE.md",
    ".loop/REPORT.md",
    ".loop/ACCEPTANCE.md",
    ".loop/REVIEW.md",
    ".loop/AUTOMATION_HANDOFF.md",
    ".loop/REVIEW_CONTEXT.json",
}


class ContractError(ValueError):
    pass


class GateError(ValueError):
    pass


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


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
        source = kit / "scripts" / name
        if source.exists():
            copy_file(source, project / "scripts" / name)
    init(project)
    print(f"installed loop loop loop runtime into {project}")


def init(project: Path) -> None:
    loop_dir = project / ".loop"
    for name in ("reports", "evidence", "reviews", "tmp", "contract-history"):
        (loop_dir / name).mkdir(parents=True, exist_ok=True)

    template_dir = project / "templates"
    if not template_dir.exists():
        template_dir = kit_root() / "templates"
    for name in TEMPLATES:
        target = loop_dir / name
        source = template_dir / name
        if not target.exists() and source.exists():
            target.write_text(source.read_text(encoding="utf-8"), encoding="utf-8")

    print(f"initialized {loop_dir}")


def text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore") if path.exists() else ""


def load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ContractError(f"missing file: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ContractError(f"invalid JSON in {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ContractError(f"expected JSON object in {path}")
    return value


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def canonical_json_hash(value: Any) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return sha256_bytes(payload)


def goal_hash(project: Path) -> str:
    body = text(project / ".loop" / "GOAL.md") + "\n" + text(project / ".loop" / "GOALS.md")
    return sha256_bytes(body.encode("utf-8"))


def policy_fingerprint(project: Path) -> str:
    rows: list[str] = []
    for rel in POLICY_FILES:
        path = project / rel
        if not path.exists():
            rows.append(f"{rel}:MISSING")
            continue
        rows.append(f"{rel}:{sha256_file(path)}")
    return sha256_bytes("\n".join(rows).encode("utf-8"))


def should_fingerprint(rel: str) -> bool:
    normalized = rel.replace("\\", "/")
    if normalized in VOLATILE_FILES:
        return False
    return not any(normalized.startswith(prefix) for prefix in VOLATILE_PREFIXES)


def workspace_fingerprint(project: Path) -> str:
    rows: list[str] = []
    for path in sorted(project.rglob("*")):
        if not path.is_file():
            continue
        rel = str(path.relative_to(project)).replace("\\", "/")
        if not should_fingerprint(rel):
            continue
        try:
            size = path.stat().st_size
            digest = sha256_file(path) if size <= 5_000_000 else f"large:{size}:{path.stat().st_mtime_ns}"
        except OSError:
            continue
        rows.append(f"{rel}:{digest}")
    return sha256_bytes("\n".join(rows).encode("utf-8"))


def contract_path(project: Path) -> Path:
    return project / ".loop" / "ACCEPTANCE_CONTRACT.json"


def lock_path(project: Path) -> Path:
    return project / ".loop" / "contract.lock.json"


def ledger_path(project: Path) -> Path:
    return project / ".loop" / "EVIDENCE_LEDGER.jsonl"


def ledger_hash(project: Path) -> str:
    path = ledger_path(project)
    return sha256_file(path) if path.exists() else sha256_bytes(b"")


def meaningful(value: Any) -> bool:
    return isinstance(value, str) and len(value.strip()) >= 8 and not PLACEHOLDER_RE.search(value)


def validate_contract(contract: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if contract.get("contract_version") != 1:
        errors.append("contract_version must be 1")
    if contract.get("status") not in {"DRAFT", "FROZEN"}:
        errors.append("status must be DRAFT or FROZEN")
    if contract.get("risk_level") not in {"L0", "L1", "L2", "L3", "L4"}:
        errors.append("risk_level must be L0-L4")
    if not meaningful(contract.get("user_intent")):
        errors.append("user_intent is missing or still a placeholder")

    modalities = contract.get("artifact_modalities")
    if not isinstance(modalities, list) or not modalities:
        errors.append("artifact_modalities must be a non-empty array")
    else:
        unknown = sorted(set(modalities) - ALLOWED_MODALITIES)
        if unknown:
            errors.append(f"unknown artifact modalities: {unknown}")

    scenarios = contract.get("scenarios")
    scenario_ids: set[str] = set()
    if not isinstance(scenarios, list) or not scenarios:
        errors.append("at least one scenario is required")
    else:
        for item in scenarios:
            if not isinstance(item, dict):
                errors.append("scenario entries must be objects")
                continue
            sid = item.get("id")
            if not isinstance(sid, str) or not re.fullmatch(r"SCN-[A-Za-z0-9_-]+", sid):
                errors.append(f"invalid scenario id: {sid!r}")
            elif sid in scenario_ids:
                errors.append(f"duplicate scenario id: {sid}")
            else:
                scenario_ids.add(sid)
            if not meaningful(item.get("description")):
                errors.append(f"scenario {sid or '?'} needs an observable description")

    outcomes = contract.get("outcomes")
    outcome_ids: set[str] = set()
    if not isinstance(outcomes, list) or not outcomes:
        errors.append("at least one observable outcome is required")
    else:
        for item in outcomes:
            if not isinstance(item, dict):
                errors.append("outcome entries must be objects")
                continue
            oid = item.get("id")
            if not isinstance(oid, str) or not re.fullmatch(r"OUT-[A-Za-z0-9_-]+", oid):
                errors.append(f"invalid outcome id: {oid!r}")
            elif oid in outcome_ids:
                errors.append(f"duplicate outcome id: {oid}")
            else:
                outcome_ids.add(oid)
            if not meaningful(item.get("description")):
                errors.append(f"outcome {oid or '?'} needs a directly observable description")
            covered = item.get("scenarios")
            if not isinstance(covered, list) or not covered:
                errors.append(f"outcome {oid or '?'} must name covered scenarios")
            elif "all" not in covered:
                unknown = sorted(set(covered) - scenario_ids)
                if unknown:
                    errors.append(f"outcome {oid or '?'} references unknown scenarios: {unknown}")
            evidence_types = item.get("evidence_types")
            if not isinstance(evidence_types, list) or not evidence_types:
                errors.append(f"outcome {oid or '?'} must declare direct evidence types")

    prohibited = contract.get("prohibited_failures")
    if not isinstance(prohibited, list) or not prohibited:
        errors.append("at least one prohibited failure is required")
    else:
        for item in prohibited:
            if not isinstance(item, dict) or not meaningful(item.get("description")):
                errors.append("prohibited failures need non-placeholder descriptions")

    proxies = contract.get("forbidden_proxies")
    if not isinstance(proxies, list) or not proxies or not all(meaningful(item) for item in proxies):
        errors.append("forbidden_proxies must contain explicit non-placeholder process proxies")

    gates = contract.get("gates")
    if not isinstance(gates, dict):
        errors.append("gates object is required")
    else:
        if gates.get("independent_review") is not True:
            errors.append("independent_review gate must be true")
        if gates.get("challenge") is not True:
            errors.append("challenge gate must be true")
        if gates.get("human_review") not in {"optional", "risk_based", "required"}:
            errors.append("human_review must be optional, risk_based, or required")

    return errors


def freeze_contract(project: Path, created_by: str = "runtime") -> tuple[bool, dict[str, Any] | list[str]]:
    path = contract_path(project)
    try:
        contract = load_json(path)
    except ContractError as exc:
        return False, [str(exc)]

    existing_lock: dict[str, Any] | None = None
    if lock_path(project).exists():
        try:
            existing_lock = load_json(lock_path(project))
        except ContractError as exc:
            return False, [str(exc)]
        current_hash = canonical_json_hash(contract)
        if existing_lock.get("contract_hash") != current_hash:
            return False, [
                "contract drift detected; do not silently re-freeze",
                "archive the old contract and create an explicit change request before replacing the lock",
            ]
        return True, existing_lock

    errors = validate_contract(contract)
    if errors:
        return False, errors

    contract["status"] = "FROZEN"
    change_control = contract.setdefault("change_control", {})
    if not isinstance(change_control, dict):
        change_control = {}
        contract["change_control"] = change_control
    change_control["frozen"] = True
    change_control["frozen_at"] = now_iso()
    change_control["frozen_by"] = created_by
    write_json(path, contract)

    lock = {
        "lock_version": 1,
        "contract_hash": canonical_json_hash(contract),
        "goal_hash": goal_hash(project),
        "policy_hash": policy_fingerprint(project),
        "frozen_at": now_iso(),
        "frozen_by": created_by,
    }
    write_json(lock_path(project), lock)
    return True, lock


def contract_status(project: Path) -> dict[str, Any]:
    result: dict[str, Any] = {
        "ready": False,
        "contract_exists": contract_path(project).exists(),
        "lock_exists": lock_path(project).exists(),
        "errors": [],
    }
    if not result["contract_exists"]:
        result["errors"].append("acceptance contract missing")
        return result
    try:
        contract = load_json(contract_path(project))
    except ContractError as exc:
        result["errors"].append(str(exc))
        return result
    result["contract"] = contract
    result["errors"].extend(validate_contract(contract))
    if not result["lock_exists"]:
        result["errors"].append("acceptance contract is not frozen")
        return result
    try:
        lock = load_json(lock_path(project))
    except ContractError as exc:
        result["errors"].append(str(exc))
        return result
    result["lock"] = lock
    if lock.get("contract_hash") != canonical_json_hash(contract):
        result["errors"].append("CONTRACT_DRIFT")
    if lock.get("policy_hash") != policy_fingerprint(project):
        result["errors"].append("POLICY_DRIFT")
    if contract.get("status") != "FROZEN" or contract.get("change_control", {}).get("frozen") is not True:
        result["errors"].append("contract file is not marked FROZEN")
    result["ready"] = not result["errors"]
    return result


def goal_is_meaningful(project: Path) -> bool:
    body = text(project / ".loop" / "GOAL.md")
    return len(body.strip()) >= 40 and not PLACEHOLDER_RE.search(body)


def frame_prompt(project: Path) -> str:
    return f"""You are the independent framing agent for Loop.

Read `.loop/GOAL.md`, `.loop/GOALS.md`, the project structure, and relevant product artifacts.
Do not implement, edit, test, or approve the project. Produce only a machine-readable acceptance contract.

The contract must:
- translate the user's real goal into directly observable outcomes;
- cover realistic states and boundary scenarios, not only the default state;
- name the artifact modalities from: {sorted(ALLOWED_MODALITIES)};
- require direct evidence appropriate to each modality;
- list process proxies that cannot prove completion;
- require independent review and adversarial challenge;
- choose risk level L0-L4 and risk-based human review;
- use status DRAFT and contract_version 1.

Avoid placeholders. The output must conform to `.codex/runtime/acceptance_contract.schema.json`.
Project root: {project}
"""


def frame(project: Path) -> int:
    init(project)
    if not goal_is_meaningful(project):
        print("GOAL.md is still a placeholder; define the real user outcome before framing.", file=sys.stderr)
        return 3
    prompt_body = frame_prompt(project)
    if os.environ.get("CODEX_DRY_RUN") == "1":
        print(prompt_body)
        return 0
    schema = project / ".codex" / "runtime" / "acceptance_contract.schema.json"
    with tempfile.NamedTemporaryFile(prefix="loop-contract-", suffix=".json", delete=False) as temp:
        output_path = Path(temp.name)
    cmd = [
        "codex",
        "exec",
        "--sandbox",
        "read-only",
        "--output-schema",
        str(schema),
        "-o",
        str(output_path),
        "-",
    ]
    try:
        code = subprocess.run(cmd, input=prompt_body, text=True, cwd=project).returncode
    except FileNotFoundError:
        print("codex CLI not found.", file=sys.stderr)
        output_path.unlink(missing_ok=True)
        return 127
    if code != 0:
        output_path.unlink(missing_ok=True)
        return code
    try:
        contract = load_json(output_path)
    except ContractError as exc:
        print(str(exc), file=sys.stderr)
        output_path.unlink(missing_ok=True)
        return 3
    output_path.unlink(missing_ok=True)
    errors = validate_contract(contract)
    if errors:
        print(json.dumps({"status": "CONTRACT_REJECTED", "errors": errors}, indent=2), file=sys.stderr)
        return 3
    write_json(contract_path(project), contract)
    ok, result = freeze_contract(project, created_by="independent_framer")
    print(json.dumps({"status": "CONTRACT_FROZEN" if ok else "CONTRACT_REJECTED", "detail": result}, indent=2))
    return 0 if ok else 3


def parse_ledger(project: Path) -> tuple[list[dict[str, Any]], list[str]]:
    records: list[dict[str, Any]] = []
    errors: list[str] = []
    path = ledger_path(project)
    if not path.exists():
        return records, ["evidence ledger missing"]
    for lineno, line in enumerate(path.read_text(encoding="utf-8", errors="ignore").splitlines(), 1):
        if not line.strip():
            continue
        try:
            item = json.loads(line)
        except json.JSONDecodeError as exc:
            errors.append(f"ledger line {lineno}: invalid JSON: {exc}")
            continue
        if not isinstance(item, dict):
            errors.append(f"ledger line {lineno}: expected object")
            continue
        records.append(item)
    return records, errors


def relative_artifact(project: Path, artifact: str) -> tuple[str, Path | None]:
    candidate = Path(artifact)
    if candidate.is_absolute():
        try:
            rel = candidate.resolve().relative_to(project)
        except ValueError:
            return artifact, None
        return str(rel).replace("\\", "/"), candidate.resolve()
    resolved = (project / candidate).resolve()
    try:
        resolved.relative_to(project)
    except ValueError:
        return artifact, None
    return str(resolved.relative_to(project)).replace("\\", "/"), resolved


def record_evidence(
    project: Path,
    claim_id: str,
    scenario_id: str,
    evidence_type: str,
    artifact: str,
    result: str,
    producer_role: str,
    notes: str,
) -> int:
    status = contract_status(project)
    if not status["ready"]:
        print(json.dumps({"status": "CONTRACT_REQUIRED", "errors": status["errors"]}, indent=2), file=sys.stderr)
        return 3
    contract = status["contract"]
    outcome = next((item for item in contract["outcomes"] if item.get("id") == claim_id), None)
    scenario = next((item for item in contract["scenarios"] if item.get("id") == scenario_id), None)
    if not outcome or not scenario:
        print("claim-id or scenario-id is not in the frozen contract", file=sys.stderr)
        return 3
    covered = outcome.get("scenarios", [])
    if "all" not in covered and scenario_id not in covered:
        print("the claim does not apply to that scenario", file=sys.stderr)
        return 3
    if evidence_type not in outcome.get("evidence_types", []):
        print("evidence-type is not allowed by the frozen outcome", file=sys.stderr)
        return 3
    rel, resolved = relative_artifact(project, artifact)
    if resolved is None or not resolved.is_file():
        print("evidence artifact must be an existing file inside the project", file=sys.stderr)
        return 3
    record = {
        "record_id": f"EV-{uuid.uuid4().hex[:12]}",
        "contract_hash": status["lock"]["contract_hash"],
        "claim_id": claim_id,
        "scenario_id": scenario_id,
        "evidence_type": evidence_type,
        "artifact": rel,
        "artifact_sha256": sha256_file(resolved),
        "result": result.upper(),
        "producer_role": producer_role,
        "notes": notes,
        "observed_at": now_iso(),
        "direct": True,
    }
    with ledger_path(project).open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")
    print(json.dumps(record, ensure_ascii=False, indent=2))
    return 0


def required_pairs(contract: dict[str, Any]) -> set[tuple[str, str]]:
    required_scenarios = {
        item["id"] for item in contract.get("scenarios", []) if item.get("required", True) is not False
    }
    pairs: set[tuple[str, str]] = set()
    for outcome in contract.get("outcomes", []):
        covered = outcome.get("scenarios", [])
        scenario_ids = required_scenarios if "all" in covered else required_scenarios.intersection(covered)
        pairs.update((outcome["id"], sid) for sid in scenario_ids)
    return pairs


def record_is_valid(project: Path, record: dict[str, Any], contract_hash: str) -> tuple[bool, str]:
    required = {
        "record_id",
        "contract_hash",
        "claim_id",
        "scenario_id",
        "evidence_type",
        "artifact",
        "artifact_sha256",
        "result",
        "producer_role",
        "observed_at",
        "direct",
    }
    missing = sorted(required - record.keys())
    if missing:
        return False, f"missing fields: {missing}"
    if record.get("contract_hash") != contract_hash:
        return False, "contract hash mismatch"
    if str(record.get("result")).upper() != "PASS":
        return False, "result is not PASS"
    if record.get("direct") is not True:
        return False, "evidence is not marked as direct observation"
    rel, artifact = relative_artifact(project, str(record.get("artifact")))
    if artifact is None or not artifact.is_file():
        return False, f"artifact missing: {rel}"
    if sha256_file(artifact) != record.get("artifact_sha256"):
        return False, f"artifact changed after observation: {rel}"
    return True, ""


def evaluate_evidence_coverage(project: Path, contract: dict[str, Any], lock: dict[str, Any]) -> dict[str, Any]:
    records, parse_errors = parse_ledger(project)
    valid_records: list[dict[str, Any]] = []
    invalid_records: list[dict[str, str]] = []
    for record in records:
        valid, reason = record_is_valid(project, record, str(lock["contract_hash"]))
        if valid:
            valid_records.append(record)
        else:
            invalid_records.append({"record_id": str(record.get("record_id", "?")), "reason": reason})

    expected = required_pairs(contract)
    observed = {(str(item.get("claim_id")), str(item.get("scenario_id"))) for item in valid_records}
    missing_pairs = sorted(expected - observed)

    type_errors: list[str] = []
    outcomes = {item["id"]: item for item in contract.get("outcomes", [])}
    for record in valid_records:
        outcome = outcomes.get(record.get("claim_id"))
        if not outcome or record.get("evidence_type") not in outcome.get("evidence_types", []):
            type_errors.append(f"{record.get('record_id')}: evidence type is not permitted by its outcome")

    modality_missing: list[str] = []
    for modality in contract.get("artifact_modalities", []):
        allowed = MODALITY_EVIDENCE.get(modality, set())
        if allowed and not any(record.get("evidence_type") in allowed for record in valid_records):
            modality_missing.append(modality)

    return {
        "complete": not parse_errors and not invalid_records and not missing_pairs and not type_errors and not modality_missing,
        "required_pairs": [list(item) for item in sorted(expected)],
        "observed_pairs": [list(item) for item in sorted(observed)],
        "missing_pairs": [list(item) for item in missing_pairs],
        "modality_missing": modality_missing,
        "parse_errors": parse_errors,
        "invalid_records": invalid_records,
        "type_errors": type_errors,
        "valid_record_ids": [item.get("record_id") for item in valid_records],
    }


def list_rel(project: Path, pattern: str) -> list[str]:
    return sorted(str(path.relative_to(project)) for path in project.glob(pattern) if path.is_file())


def git_ok(project: Path) -> bool:
    result = subprocess.run(["git", "rev-parse", "--is-inside-work-tree"], cwd=project, capture_output=True, text=True)
    return result.returncode == 0 and result.stdout.strip() == "true"


def git_head(project: Path) -> str:
    result = subprocess.run(["git", "rev-parse", "HEAD"], cwd=project, capture_output=True, text=True)
    return result.stdout.strip() if result.returncode == 0 else "NO_GIT_HEAD"


def scan_secrets(project: Path) -> list[str]:
    hits: list[str] = []
    for path in project.rglob("*"):
        if not path.is_file() or ".git" in path.parts or "__pycache__" in path.parts or path.stat().st_size > 500_000:
            continue
        try:
            for i, line in enumerate(path.read_text(encoding="utf-8", errors="ignore").splitlines(), 1):
                if SECRET_RE.search(line):
                    hits.append(f"{path.relative_to(project)}:{i}")
        except OSError:
            continue
    return hits


def capabilities(project: Path) -> dict[str, Any]:
    caps: dict[str, Any] = {
        "git": git_ok(project),
        "codex_cli": bool(shutil.which("codex")),
        "docs": list_rel(project, "README*") + list_rel(project, "AGENTS*"),
        "scripts": list_rel(project, "scripts/*"),
        "package_files": [
            name
            for name in ("package.json", "pyproject.toml", "Cargo.toml", "go.mod", "Makefile")
            if (project / name).exists()
        ],
        "project_skills": list_rel(project, ".codex/skills/*/SKILL.md"),
        "github_workflows": list_rel(project, ".github/workflows/*"),
    }
    gaps: list[str] = []
    if not caps["codex_cli"]:
        gaps.append("codex CLI unavailable")
    if not caps["scripts"]:
        gaps.append("no local scripts discovered")
    if not caps["package_files"]:
        gaps.append("no package/build manifest discovered")
    caps["recommended_agents"] = ["independent_framer", "builder", "independent_reviewer"]
    caps["known_gaps"] = gaps
    return caps


def schema_status(project: Path) -> tuple[bool, str]:
    path = project / ".codex" / "runtime" / "loop_result.schema.json"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:  # pragma: no cover - error path reported by check
        return False, f"{type(exc).__name__}: {exc}"
    expected = {
        "role",
        "status",
        "contract_hash",
        "total_score",
        "scores",
        "actions_taken",
        "verification",
        "evidence",
        "blockers",
        "experience",
        "next_run_instruction",
    }
    missing = sorted(expected - set(data.get("required", [])))
    return (not missing, f"missing required fields: {missing}" if missing else "")


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
        "contract": contract_status(project),
        "codex_cli": bool(shutil.which("codex")),
        "git_repo": git_ok(project),
        "capabilities": capabilities(project),
        "secret_hits": scan_secrets(project),
    }
    print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
    return 0 if result["runtime_ok"] and result["schema_ok"] and result["state_ok"] and not result["secret_hits"] else 1


def write_capabilities(project: Path, caps: dict[str, Any]) -> None:
    body = ["# Capabilities", "", "## Local Scan", "", "```json", json.dumps(caps, ensure_ascii=False, indent=2), "```", ""]
    (project / ".loop" / "CAPABILITIES.md").write_text("\n".join(body), encoding="utf-8")


def discover(project: Path) -> int:
    init(project)
    caps = capabilities(project)
    write_capabilities(project, caps)
    print(json.dumps(caps, ensure_ascii=False, indent=2))
    return 0


def latest_worker_report(project: Path) -> dict[str, Any] | None:
    reports = sorted((project / ".loop" / "reports").glob("worker-*.json"), reverse=True)
    for path in reports:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if isinstance(data, dict):
            data["_path"] = str(path.relative_to(project)).replace("\\", "/")
            return data
    return None


def parse_scores_from_report(report: dict[str, Any] | None) -> dict[str, float]:
    scores: dict[str, float] = {}
    source = report.get("scores", {}) if report else {}
    for key, (maximum, _) in SCORE_FIELDS.items():
        value = source.get(key, 0) if isinstance(source, dict) else 0
        try:
            scores[key] = max(0.0, min(float(maximum), float(value)))
        except (TypeError, ValueError):
            scores[key] = 0.0
    return scores


def score_data(project: Path) -> dict[str, Any]:
    report = latest_worker_report(project)
    status = contract_status(project)
    scores = parse_scores_from_report(report)
    total = sum(scores.values())
    coverage = (
        evaluate_evidence_coverage(project, status["contract"], status["lock"])
        if status.get("ready")
        else {"complete": False, "missing_pairs": [], "modality_missing": [], "parse_errors": status["errors"]}
    )
    blocked = bool(report and report.get("status") == "BLOCKED")
    automation_verified = bool(
        status.get("ready")
        and coverage.get("complete")
        and report
        and report.get("role") == "worker"
        and report.get("contract_hash") == status["lock"]["contract_hash"]
        and report.get("status") == "AUTOMATION_VERIFIED"
    )
    lifecycle = "BLOCKED" if blocked else ("AUTOMATION_VERIFIED" if automation_verified else "IMPLEMENTED")
    deductions = sorted(
        ({"field": key, "deduction": maximum - scores[key]} for key, (maximum, _) in SCORE_FIELDS.items()),
        key=lambda item: item["deduction"],
        reverse=True,
    )
    return {
        "status": lifecycle,
        "total_score": total,
        "scores": scores,
        "highest_deductions": deductions[:3],
        "coverage": coverage,
        "worker_report": report.get("_path") if report else None,
        "note": "score is diagnostic only and cannot promote acceptance",
    }


def score(project: Path) -> int:
    print(json.dumps(score_data(project), ensure_ascii=False, indent=2))
    return 0


def worker_prompt(project: Path) -> str:
    status = contract_status(project)
    contract_hash = status.get("lock", {}).get("contract_hash", "UNFROZEN")
    return f"""Start Loop Runtime as the worker.

Read `.codex/runtime/INDEX.md`, `.loop/GOAL.md`, `.loop/GOALS.md`, and the frozen `.loop/ACCEPTANCE_CONTRACT.json`.
Contract hash: {contract_hash}

Run exactly one worker loop: Recover -> Discover -> Pick -> Execute -> Observe -> Verify -> Record.
You may implement and repair, but you may not approve your own work.
Do not modify the acceptance contract, contract lock, runtime policy files, review files, or weaken existing checks.
Treat `.loop/REPORT.md`, scores, builds, logs, and screenshot counts as claims, never as acceptance proof.
Record direct claim/scenario evidence with `python scripts/loop.py record-evidence ...`.
Read `.loop/REVIEW.md` for prior independent findings, but do not edit it.
Return only IMPLEMENTED, AUTOMATION_VERIFIED, PARTIALLY_VERIFIED, or BLOCKED using `.codex/runtime/loop_result.schema.json`.
Never claim CANDIDATE_PASS, ACCEPTED, release approval, merge, publish, deploy, payment, credential use, or destructive completion.
Project root: {project}
"""


def run_worker(project: Path) -> int:
    init(project)
    status = contract_status(project)
    if not status["ready"]:
        print(json.dumps({"status": "CONTRACT_REQUIRED", "errors": status["errors"]}, indent=2), file=sys.stderr)
        return 3
    prompt_body = worker_prompt(project)
    if os.environ.get("CODEX_DRY_RUN") == "1":
        print(prompt_body)
        return 0
    sandbox = os.environ.get("CODEX_SANDBOX", "workspace-write")
    report = project / ".loop" / "reports" / f"worker-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
    schema = project / ".codex" / "runtime" / "loop_result.schema.json"
    cmd = ["codex", "exec", "--sandbox", sandbox, "--output-schema", str(schema), "-o", str(report), "-"]
    try:
        return subprocess.run(cmd, input=prompt_body, text=True, cwd=project).returncode
    except FileNotFoundError:
        print("codex CLI not found. Set CODEX_DRY_RUN=1 to inspect prompts.", file=sys.stderr)
        return 127


def review_context(project: Path) -> dict[str, Any]:
    status = contract_status(project)
    if not status["ready"]:
        raise GateError("contract is not frozen and stable")
    coverage = evaluate_evidence_coverage(project, status["contract"], status["lock"])
    context = {
        "review_context_id": f"RVCTX-{uuid.uuid4().hex[:12]}",
        "created_at": now_iso(),
        "contract_hash": status["lock"]["contract_hash"],
        "policy_hash": status["lock"]["policy_hash"],
        "workspace_fingerprint": workspace_fingerprint(project),
        "evidence_ledger_hash": ledger_hash(project),
        "git_head": git_head(project),
        "required_pairs": coverage["required_pairs"],
        "artifact_modalities": status["contract"].get("artifact_modalities", []),
        "denied_claim_sources": [
            ".loop/REPORT.md self-evaluation",
            ".loop/STATE.md completion language",
            "worker scores",
            "build success without direct outcome evidence",
            "evidence quantity without inspection",
        ],
    }
    write_json(project / ".loop" / "REVIEW_CONTEXT.json", context)
    return context


def review_prompt(project: Path, context: dict[str, Any]) -> str:
    return f"""You are Loop's independent read-only reviewer and adversarial challenger.

This is a fresh review process. You did not implement the candidate. Do not edit any file, test, rule, contract, or artifact.
Review the final observable result against `.loop/ACCEPTANCE_CONTRACT.json` and `.loop/REVIEW_CONTEXT.json`.
Review context id: {context['review_context_id']}
Contract hash: {context['contract_hash']}
Policy hash: {context['policy_hash']}
Workspace fingerprint: {context['workspace_fingerprint']}
Evidence ledger hash: {context['evidence_ledger_hash']}

Rules:
- Treat worker reports, scores, build success, console cleanliness, screenshot counts, and completion language only as untrusted claims.
- Inspect actual artifacts and direct evidence for every required outcome/scenario pair.
- Reject stale, missing, changed, indirect, or semantically irrelevant evidence.
- Use the artifact-appropriate modality: visual artifacts require rendered visual inspection; code requires runtime or behavioral checks; data requires recomputation/cross-checks; documents require rendered inspection; automation requires end-to-end state verification; research requires source cross-checking.
- Actively try to falsify the candidate. Include at least one challenge case per artifact modality.
- Check combinations and semantic consistency, not only isolated fields.
- A PASS requires all required claims and scenarios to pass, no P0/P1 finding, challenge PASS, and no unresolved material uncertainty.
- Set reviewer_role to independent_reviewer and self_review to false.
- Copy the exact context hashes into the result.

Output only JSON conforming to `.codex/runtime/review_result.schema.json`.
Project root: {project}
"""


def validate_review_result(data: dict[str, Any], context: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for field in ("review_context_id", "contract_hash", "policy_hash", "workspace_fingerprint", "evidence_ledger_hash"):
        if data.get(field) != context.get(field):
            errors.append(f"{field} does not match the runtime review context")
    if data.get("reviewer_role") != "independent_reviewer":
        errors.append("reviewer_role must be independent_reviewer")
    if data.get("self_review") is not False:
        errors.append("self_review must be false")
    if data.get("verdict") not in {"PASS", "FAIL", "BLOCKED"}:
        errors.append("invalid review verdict")
    challenge = data.get("challenge")
    if not isinstance(challenge, dict):
        errors.append("challenge object missing")
    return errors


def review(project: Path) -> int:
    init(project)
    try:
        context = review_context(project)
    except GateError as exc:
        print(str(exc), file=sys.stderr)
        return 3
    prompt_body = review_prompt(project, context)
    if os.environ.get("CODEX_DRY_RUN") == "1":
        print(prompt_body)
        return 0
    schema = project / ".codex" / "runtime" / "review_result.schema.json"
    with tempfile.NamedTemporaryFile(prefix="loop-review-", suffix=".json", delete=False) as temp:
        output_path = Path(temp.name)
    cmd = ["codex", "exec", "--sandbox", "read-only", "--output-schema", str(schema), "-o", str(output_path), "-"]
    try:
        code = subprocess.run(cmd, input=prompt_body, text=True, cwd=project).returncode
    except FileNotFoundError:
        print("codex CLI not found.", file=sys.stderr)
        output_path.unlink(missing_ok=True)
        return 127
    if code != 0:
        output_path.unlink(missing_ok=True)
        return code
    try:
        data = load_json(output_path)
    except ContractError as exc:
        print(str(exc), file=sys.stderr)
        output_path.unlink(missing_ok=True)
        return 3
    output_path.unlink(missing_ok=True)
    errors = validate_review_result(data, context)
    if errors:
        print(json.dumps({"status": "REVIEW_REJECTED", "errors": errors}, indent=2), file=sys.stderr)
        return 3

    review_file = project / ".loop" / "reviews" / f"review-{datetime.now().strftime('%Y%m%d-%H%M%S')}-{context['review_context_id']}.json"
    write_json(review_file, data)
    receipt = {
        "receipt_version": 1,
        "created_at": now_iso(),
        "mode": "separate_codex_exec_read_only",
        "review_file": str(review_file.relative_to(project)).replace("\\", "/"),
        "review_sha256": sha256_file(review_file),
        "review_context": context,
    }
    receipt_file = review_file.with_suffix(".receipt.json")
    write_json(receipt_file, receipt)
    write_review_summary(project, data, receipt)
    print(json.dumps({"status": "REVIEW_RECORDED", "review": receipt["review_file"], "verdict": data["verdict"]}, indent=2))
    return 0


def write_review_summary(project: Path, data: dict[str, Any], receipt: dict[str, Any]) -> None:
    findings = data.get("findings", [])
    lines = [
        "# Independent Review",
        "",
        f"verdict: {data.get('verdict')}",
        f"review_file: {receipt.get('review_file')}",
        f"review_context_id: {data.get('review_context_id')}",
        "",
        "## Findings",
        "",
    ]
    if findings:
        for finding in findings:
            lines.append(f"- {finding.get('severity', '?')}: {finding.get('summary', '')}")
    else:
        lines.append("- None recorded.")
    lines += ["", "## Next Action", "", str(data.get("next_action", "Re-run the policy gate.")), ""]
    (project / ".loop" / "REVIEW.md").write_text("\n".join(lines), encoding="utf-8")


def latest_review_receipt(project: Path) -> tuple[dict[str, Any] | None, dict[str, Any] | None, list[str]]:
    errors: list[str] = []
    receipts = sorted((project / ".loop" / "reviews").glob("review-*.receipt.json"), reverse=True)
    if not receipts:
        return None, None, ["no independent review receipt"]
    try:
        receipt = load_json(receipts[0])
    except ContractError as exc:
        return None, None, [str(exc)]
    review_rel = receipt.get("review_file")
    if not isinstance(review_rel, str):
        return receipt, None, ["review receipt has no review_file"]
    review_path = project / review_rel
    if not review_path.is_file():
        return receipt, None, ["review file referenced by receipt is missing"]
    if sha256_file(review_path) != receipt.get("review_sha256"):
        errors.append("review file changed after receipt")
    try:
        review_data = load_json(review_path)
    except ContractError as exc:
        errors.append(str(exc))
        return receipt, None, errors
    return receipt, review_data, errors


def review_claim_pairs(review_data: dict[str, Any]) -> set[tuple[str, str]]:
    pairs: set[tuple[str, str]] = set()
    for claim in review_data.get("claims", []):
        if isinstance(claim, dict) and claim.get("verdict") == "PASS":
            pairs.add((str(claim.get("claim_id")), str(claim.get("scenario_id"))))
    return pairs


def valid_evidence_artifacts_by_pair(
    project: Path,
    contract_hash: str,
) -> dict[tuple[str, str], set[str]]:
    records, _ = parse_ledger(project)
    artifacts: dict[tuple[str, str], set[str]] = {}
    for record in records:
        valid, _ = record_is_valid(project, record, contract_hash)
        if not valid:
            continue
        rel, path = relative_artifact(project, str(record.get("artifact", "")))
        if path is None:
            continue
        pair = (str(record.get("claim_id")), str(record.get("scenario_id")))
        artifacts.setdefault(pair, set()).add(rel)
    return artifacts


def normalized_evidence_refs(project: Path, refs: Any) -> set[str]:
    if not isinstance(refs, list):
        return set()
    normalized: set[str] = set()
    for ref in refs:
        if not isinstance(ref, str):
            continue
        rel, path = relative_artifact(project, ref)
        if path is not None:
            normalized.add(rel)
    return normalized


def policy_gate(project: Path) -> dict[str, Any]:
    status = contract_status(project)
    reasons: list[str] = list(status["errors"])
    if not status["ready"]:
        lifecycle = "CONTRACT_DRIFT" if any("DRIFT" in item for item in reasons) else "CONTRACT_REQUIRED"
        return gate_result(lifecycle, "CANDIDATE_PARTIAL", reasons, {})

    contract = status["contract"]
    lock = status["lock"]
    coverage = evaluate_evidence_coverage(project, contract, lock)
    if not coverage["complete"]:
        reasons.append("direct evidence coverage is incomplete")
        return gate_result("NEEDS_EVIDENCE", "CANDIDATE_PARTIAL", reasons, {"coverage": coverage})

    receipt, review_data, review_errors = latest_review_receipt(project)
    if review_errors or not receipt or not review_data:
        reasons.extend(review_errors)
        return gate_result("NEEDS_INDEPENDENT_REVIEW", "CANDIDATE_PARTIAL", reasons, {"coverage": coverage})

    context = receipt.get("review_context", {})
    current = {
        "contract_hash": lock["contract_hash"],
        "policy_hash": lock["policy_hash"],
        "workspace_fingerprint": workspace_fingerprint(project),
        "evidence_ledger_hash": ledger_hash(project),
    }
    for field, expected in current.items():
        if context.get(field) != expected or review_data.get(field) != expected:
            reasons.append(f"stale independent review: {field} changed")
    if receipt.get("mode") != "separate_codex_exec_read_only":
        reasons.append("review was not produced by a separate read-only process")
    if review_data.get("reviewer_role") != "independent_reviewer" or review_data.get("self_review") is not False:
        reasons.append("review is not independent")

    expected_pairs = required_pairs(contract)
    missing_review_pairs = sorted(expected_pairs - review_claim_pairs(review_data))
    if missing_review_pairs:
        reasons.append(f"review did not pass required claim/scenario pairs: {missing_review_pairs}")

    evidence_by_pair = valid_evidence_artifacts_by_pair(project, str(lock["contract_hash"]))
    for pair in sorted(expected_pairs):
        passing_claims = [
            claim
            for claim in review_data.get("claims", [])
            if isinstance(claim, dict)
            and claim.get("verdict") == "PASS"
            and (str(claim.get("claim_id")), str(claim.get("scenario_id"))) == pair
        ]
        allowed_artifacts = evidence_by_pair.get(pair, set())
        if passing_claims and not any(
            normalized_evidence_refs(project, claim.get("evidence_refs")) & allowed_artifacts
            for claim in passing_claims
        ):
            reasons.append(f"review PASS is not bound to valid evidence for claim/scenario pair: {pair}")

    findings = review_data.get("findings", [])
    severe = [item for item in findings if isinstance(item, dict) and item.get("severity") in {"P0", "P1"}]
    if severe:
        reasons.append("independent review contains P0/P1 findings")

    challenge = review_data.get("challenge", {}) if isinstance(review_data.get("challenge"), dict) else {}
    if challenge.get("attempted") is not True or challenge.get("verdict") != "PASS":
        reasons.append("challenge gate did not pass")
    challenge_modalities = {
        item.get("modality")
        for item in challenge.get("cases", [])
        if isinstance(item, dict) and item.get("verdict") == "PASS"
    }
    missing_challenges = sorted(set(contract.get("artifact_modalities", [])) - challenge_modalities)
    if missing_challenges:
        reasons.append(f"no passing challenge case for modalities: {missing_challenges}")
    valid_artifacts = set().union(*evidence_by_pair.values()) if evidence_by_pair else set()
    for case in challenge.get("cases", []):
        if not isinstance(case, dict) or case.get("verdict") != "PASS":
            continue
        if not normalized_evidence_refs(project, case.get("evidence_refs")) & valid_artifacts:
            reasons.append(f"passing challenge {case.get('id', '?')} is not bound to valid evidence")

    remaining_uncertainty = review_data.get("remaining_uncertainty", [])
    if isinstance(remaining_uncertainty, list) and any(str(item).strip() for item in remaining_uncertainty):
        reasons.append("independent review contains unresolved uncertainty")

    if review_data.get("verdict") != "PASS":
        reasons.append(f"independent reviewer verdict is {review_data.get('verdict')}")

    if reasons:
        return gate_result(
            "REVIEW_FAILED",
            "CANDIDATE_REJECTED",
            reasons,
            {"coverage": coverage, "review_file": receipt.get("review_file")},
        )

    human_mode = contract.get("gates", {}).get("human_review")
    risk = contract.get("risk_level")
    human_required = human_mode == "required" or (human_mode == "risk_based" and risk in {"L3", "L4"})
    if human_required:
        return gate_result(
            "NEEDS_HUMAN",
            "CANDIDATE_PARTIAL",
            [f"risk level {risk} requires explicit human acceptance"],
            {"coverage": coverage, "review_file": receipt.get("review_file")},
        )

    return gate_result(
        "INDEPENDENTLY_VERIFIED",
        "CANDIDATE_PASS",
        [],
        {"coverage": coverage, "review_file": receipt.get("review_file")},
    )


def gate_result(lifecycle: str, candidate_status: str, reasons: list[str], evidence: dict[str, Any]) -> dict[str, Any]:
    return {
        "lifecycle_status": lifecycle,
        "candidate_status": candidate_status,
        "accepted": lifecycle == "INDEPENDENTLY_VERIFIED",
        "reasons": reasons,
        "evidence": evidence,
        "evaluated_at": now_iso(),
    }


def write_gate_outputs(project: Path, result: dict[str, Any]) -> None:
    reasons = result.get("reasons", [])
    lines = [
        "# Acceptance",
        "",
        f"lifecycle_status: {result.get('lifecycle_status')}",
        f"candidate_status: {result.get('candidate_status')}",
        f"accepted: {str(result.get('accepted')).lower()}",
        f"evaluated_at: {result.get('evaluated_at')}",
        "",
        "## Reasons",
        "",
    ]
    lines.extend(f"- {item}" for item in reasons) if reasons else lines.append("- All configured evidence and independent gates passed.")
    lines += ["", "## Evidence", "", "```json", json.dumps(result.get("evidence", {}), ensure_ascii=False, indent=2), "```", ""]
    (project / ".loop" / "ACCEPTANCE.md").write_text("\n".join(lines), encoding="utf-8")


def gate(project: Path) -> int:
    result = policy_gate(project)
    write_gate_outputs(project, result)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if result["lifecycle_status"] == "INDEPENDENTLY_VERIFIED":
        return 0
    if result["lifecycle_status"] == "NEEDS_HUMAN":
        return 4
    return 2


def write_automation_handoff(project: Path, status: str, next_command: str) -> None:
    body = [
        "# Automation Handoff",
        "",
        f"status: {status}",
        f"updated_at: {now_iso()}",
        "",
        "## Next Command",
        "",
        f"`{next_command}`",
        "",
        "## Stop Conditions",
        "",
        "- INDEPENDENTLY_VERIFIED",
        "- NEEDS_HUMAN",
        "- BLOCKED",
        "- CONTRACT_DRIFT or POLICY_DRIFT",
        "- max iterations reached",
        "",
    ]
    (project / ".loop" / "AUTOMATION_HANDOFF.md").write_text("\n".join(body), encoding="utf-8")


def run_loop(project: Path, max_iterations: int) -> int:
    init(project)
    status = contract_status(project)
    if not status["ready"]:
        if status["errors"] == ["acceptance contract is not frozen"] or not lock_path(project).exists():
            frame_code = frame(project)
            if frame_code != 0 or os.environ.get("CODEX_DRY_RUN") == "1":
                return frame_code
        else:
            print(json.dumps({"status": "CONTRACT_OR_POLICY_DRIFT", "errors": status["errors"]}, indent=2), file=sys.stderr)
            return 3

    iterations = 1 if os.environ.get("CODEX_DRY_RUN") == "1" else max_iterations
    for iteration in range(1, iterations + 1):
        print(f"loop iteration {iteration}/{iterations}")
        code = run_worker(project)
        if code != 0:
            return code
        if os.environ.get("CODEX_DRY_RUN") == "1":
            write_automation_handoff(project, "IMPLEMENTED", "python scripts/loop.py run-loop . --max-iterations 10")
            return 0

        automation = score_data(project)
        print(json.dumps(automation, ensure_ascii=False, indent=2))
        if automation["status"] == "BLOCKED":
            write_automation_handoff(project, "BLOCKED", "Resolve the smallest blocker, then rerun the loop.")
            return 2
        if automation["status"] != "AUTOMATION_VERIFIED":
            continue

        code = review(project)
        if code != 0:
            return code
        result = policy_gate(project)
        write_gate_outputs(project, result)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        if result["lifecycle_status"] == "INDEPENDENTLY_VERIFIED":
            write_automation_handoff(project, "INDEPENDENTLY_VERIFIED", "Review evidence before any release, merge, or deploy action.")
            return 0
        if result["lifecycle_status"] == "NEEDS_HUMAN":
            write_automation_handoff(project, "NEEDS_HUMAN", "Obtain explicit human acceptance; do not auto-promote.")
            return 4

    write_automation_handoff(project, "PARTIALLY_VERIFIED", "python scripts/loop.py run-loop . --max-iterations 10")
    return 2


def distill_experience(project: Path) -> int:
    source = project / ".loop" / "EXPERIENCE.md"
    candidates = project / ".loop" / "skill-candidates"
    candidates.mkdir(exist_ok=True)
    lines = [line.strip("- ").strip() for line in text(source).splitlines() if line.strip().startswith("- ") and len(line.strip()) > 6]
    counts: dict[str, int] = {}
    for line in lines:
        counts[line] = counts.get(line, 0) + 1
    repeated = [line for line, count in counts.items() if count >= 2]
    if not repeated:
        print("No repeated experience found; no candidate skill written.")
        return 0
    skill = candidates / "generated-loop-patterns.SKILL.md"
    body = [
        "---",
        "name: generated-loop-patterns",
        "description: Candidate skill distilled from repeated local loop experience.",
        "---",
        "",
        "# Generated Loop Patterns",
        "",
        "Review before promoting this candidate skill.",
        "",
    ]
    body.extend(f"- {line}" for line in repeated)
    skill.write_text("\n".join(body) + "\n", encoding="utf-8")
    print(f"wrote {skill}")
    return 0


def prompt() -> None:
    print(
        "Start Runtime.\n"
        "Read `.codex/runtime/INDEX.md`.\n"
        "Recover `.loop/STATE.md`, `.loop/GOAL.md`, and the frozen acceptance contract.\n"
        "Continue one evidence-gated loop.\n"
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="loop loop loop evidence-gated runtime")
    parser.add_argument(
        "command",
        choices=[
            "install",
            "init",
            "prompt",
            "check",
            "discover",
            "frame",
            "freeze-contract",
            "record-evidence",
            "score",
            "review",
            "gate",
            "distill-experience",
            "run",
            "run-loop",
        ],
    )
    parser.add_argument("project", nargs="?", default=".")
    parser.add_argument("--max-iterations", type=int, default=10)
    parser.add_argument("--claim-id")
    parser.add_argument("--scenario-id")
    parser.add_argument("--evidence-type")
    parser.add_argument("--artifact")
    parser.add_argument("--result", choices=["PASS", "FAIL"], default="PASS")
    parser.add_argument("--producer-role", default="worker")
    parser.add_argument("--notes", default="")
    return parser


def main() -> int:
    args = build_parser().parse_args()
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
    if args.command == "discover":
        return discover(project)
    if args.command == "frame":
        return frame(project)
    if args.command == "freeze-contract":
        ok, result = freeze_contract(project, created_by="explicit_freeze_command")
        print(json.dumps({"status": "CONTRACT_FROZEN" if ok else "CONTRACT_REJECTED", "detail": result}, indent=2))
        return 0 if ok else 3
    if args.command == "record-evidence":
        required = {
            "--claim-id": args.claim_id,
            "--scenario-id": args.scenario_id,
            "--evidence-type": args.evidence_type,
            "--artifact": args.artifact,
        }
        missing = [flag for flag, value in required.items() if not value]
        if missing:
            print(f"missing required arguments: {', '.join(missing)}", file=sys.stderr)
            return 3
        return record_evidence(
            project,
            args.claim_id,
            args.scenario_id,
            args.evidence_type,
            args.artifact,
            args.result,
            args.producer_role,
            args.notes,
        )
    if args.command == "score":
        return score(project)
    if args.command == "review":
        return review(project)
    if args.command == "gate":
        return gate(project)
    if args.command == "distill-experience":
        return distill_experience(project)
    if args.command == "run-loop":
        return run_loop(project, args.max_iterations)
    return run_worker(project)


if __name__ == "__main__":
    raise SystemExit(main())
