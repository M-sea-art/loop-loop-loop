from __future__ import annotations

import importlib.util
import json
import shutil
import tempfile
import unittest
from unittest import mock
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("loop_runtime", ROOT / "scripts" / "loop.py")
assert SPEC and SPEC.loader
loop = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(loop)


class RuntimeTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.project = Path(self.temp.name)
        shutil.copytree(ROOT / "templates", self.project / "templates")
        shutil.copytree(ROOT / ".codex", self.project / ".codex")
        (self.project / "scripts").mkdir()
        shutil.copy2(ROOT / "scripts" / "loop.py", self.project / "scripts" / "loop.py")
        (self.project / "README.md").write_text("# Test project\n", encoding="utf-8")
        loop.init(self.project)
        (self.project / ".loop" / "GOAL.md").write_text(
            "# Goal\n\nDeliver an observable artifact that remains correct across the required operating states.\n",
            encoding="utf-8",
        )

    def tearDown(self) -> None:
        self.temp.cleanup()

    def contract(self, *, risk: str = "L2", modality: str = "code", evidence_type: str = "test") -> dict:
        return {
            "contract_version": 1,
            "contract_id": "test-contract",
            "status": "DRAFT",
            "risk_level": risk,
            "user_intent": "The user can observe the expected behavior in every required scenario.",
            "artifact_modalities": [modality],
            "outcomes": [
                {
                    "id": "OUT-001",
                    "description": "The final artifact exhibits the required behavior without hidden failure.",
                    "scenarios": ["SCN-001", "SCN-EDGE"],
                    "evidence_types": [evidence_type],
                }
            ],
            "scenarios": [
                {"id": "SCN-001", "description": "The normal operating state uses representative input.", "required": True},
                {"id": "SCN-EDGE", "description": "A boundary operating state stresses the result.", "required": True},
            ],
            "prohibited_failures": [
                {"id": "FAIL-001", "description": "Do not accept process success when the observable result fails."}
            ],
            "forbidden_proxies": [
                "Build success alone cannot prove the user's observable result."
            ],
            "gates": {
                "automation": True,
                "independent_review": True,
                "challenge": True,
                "human_review": "risk_based",
            },
            "change_control": {"frozen": False, "reason": ""},
        }

    def freeze(self, **kwargs) -> dict:
        loop.write_json(loop.contract_path(self.project), self.contract(**kwargs))
        ok, detail = loop.freeze_contract(self.project, created_by="test-framer")
        self.assertTrue(ok, detail)
        assert isinstance(detail, dict)
        return detail

    def test_init_seeds_plan_and_evidence_templates(self) -> None:
        self.assertTrue((self.project / ".loop" / "PLAN.md").is_file())
        self.assertTrue((self.project / ".loop" / "EVIDENCE.md").is_file())

    def test_install_preserves_existing_project_governance(self) -> None:
        sentinels = {
            ".loop/ACCEPTANCE_CONTRACT.json": '{"sentinel":"contract"}\n',
            ".loop/EVIDENCE_LEDGER.jsonl": '{"sentinel":"ledger"}\n',
            ".loop/contract.lock.json": '{"sentinel":"lock"}\n',
            ".looploop/project-completion-plan.md": "# Sentinel plan\n",
        }
        for relative, contents in sentinels.items():
            target = self.project / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(contents, encoding="utf-8")
        before = {relative: loop.sha256_file(self.project / relative) for relative in sentinels}

        loop.install(self.project)

        after = {relative: loop.sha256_file(self.project / relative) for relative in sentinels}
        self.assertEqual(after, before)
        for relative, contents in sentinels.items():
            self.assertEqual((self.project / relative).read_text(encoding="utf-8"), contents)

    def add_artifact_evidence(self, lock: dict, *, evidence_type: str = "test") -> None:
        for scenario in ("SCN-001", "SCN-EDGE"):
            artifact = self.project / ".loop" / "evidence" / f"{scenario}.txt"
            artifact.write_text(f"PASS {scenario}\n", encoding="utf-8")
            code = loop.record_evidence(
                self.project,
                "OUT-001",
                scenario,
                evidence_type,
                str(artifact),
                "PASS",
                "worker",
                "direct observation",
            )
            self.assertEqual(code, 0)

    def add_passing_review(self, contract: dict, lock: dict, track: str = "independent") -> None:
        context = loop.review_context(self.project, track)
        review = {
            "review_context_id": context["review_context_id"],
            "reviewer_role": "independent_reviewer",
            "reviewer_track": track,
            "self_review": False,
            "contract_hash": context["contract_hash"],
            "policy_hash": context["policy_hash"],
            "workspace_fingerprint": context["workspace_fingerprint"],
            "evidence_ledger_hash": context["evidence_ledger_hash"],
            "verdict": "PASS",
            "reviewed_artifacts": [".loop/evidence/SCN-001.txt", ".loop/evidence/SCN-EDGE.txt"],
            "claims": [
                {
                    "claim_id": "OUT-001",
                    "scenario_id": scenario,
                    "verdict": "PASS",
                    "evidence_refs": [f".loop/evidence/{scenario}.txt"],
                    "reason": "Observed the required behavior.",
                }
                for scenario in ("SCN-001", "SCN-EDGE")
            ],
            "findings": [],
            "challenge": {
                "attempted": True,
                "verdict": "PASS",
                "cases": [
                    {
                        "id": "CH-001",
                        "modality": contract["artifact_modalities"][0],
                        "target": "OUT-001 under SCN-EDGE",
                        "hypothesis": "The boundary state may invalidate the claimed behavior.",
                        "method": "Replayed the boundary evidence and inspected the artifact.",
                        "verdict": "PASS",
                        "evidence_refs": [".loop/evidence/SCN-EDGE.txt"],
                    }
                ],
            },
            "remaining_uncertainty": [],
            "next_action": "Run the policy gate.",
        }
        review_file = self.project / ".loop" / "reviews" / f"review-{track}-test.json"
        loop.write_json(review_file, review)
        receipt = {
            "receipt_version": 1,
            "created_at": loop.now_iso(),
            "mode": "separate_codex_exec_monitored_read_only",
            "reviewer_track": track,
            "review_file": str(review_file.relative_to(self.project)),
            "review_sha256": loop.sha256_file(review_file),
            "review_context": context,
            "mutation_guard": {
                "before": {
                    field: context[field]
                    for field in ("contract_hash", "policy_hash", "workspace_fingerprint", "evidence_ledger_hash")
                },
                "after": loop.review_mutation_guard(self.project, context),
            },
        }
        loop.write_json(review_file.with_suffix(".receipt.json"), receipt)

    def test_freeze_contract_and_detect_contract_drift(self) -> None:
        self.freeze()
        status = loop.contract_status(self.project)
        self.assertTrue(status["ready"], status["errors"])

        contract = loop.load_json(loop.contract_path(self.project))
        contract["user_intent"] += " Changed after freeze."
        loop.write_json(loop.contract_path(self.project), contract)
        status = loop.contract_status(self.project)
        self.assertFalse(status["ready"])
        self.assertIn("CONTRACT_DRIFT", status["errors"])

    def test_worker_score_cannot_create_acceptance(self) -> None:
        self.freeze()
        report = {
            "role": "worker",
            "status": "AUTOMATION_VERIFIED",
            "contract_hash": loop.load_json(loop.lock_path(self.project))["contract_hash"],
            "total_score": 100,
            "scores": {key: maximum for key, (maximum, _) in loop.SCORE_FIELDS.items()},
            "actions_taken": ["implemented"],
            "verification": ["build passed"],
            "evidence": ["build.log"],
            "blockers": [],
            "experience": [],
            "next_run_instruction": "approve",
        }
        loop.write_json(self.project / ".loop" / "reports" / "worker-99999999.json", report)
        scored = loop.score_data(self.project)
        self.assertNotEqual(scored["status"], "CANDIDATE_PASS")
        gated = loop.policy_gate(self.project)
        self.assertEqual(gated["lifecycle_status"], "NEEDS_EVIDENCE")
        self.assertFalse(gated["accepted"])

    def test_visual_proxy_evidence_is_rejected(self) -> None:
        lock = self.freeze(modality="visual", evidence_type="build")
        self.add_artifact_evidence(lock, evidence_type="build")
        contract = loop.load_json(loop.contract_path(self.project))
        coverage = loop.evaluate_evidence_coverage(self.project, contract, lock)
        self.assertFalse(coverage["complete"])
        self.assertEqual(coverage["modality_missing"], ["visual"])
        gated = loop.policy_gate(self.project)
        self.assertEqual(gated["lifecycle_status"], "NEEDS_EVIDENCE")

    def test_gate_requires_independent_review(self) -> None:
        lock = self.freeze()
        self.add_artifact_evidence(lock)
        result = loop.policy_gate(self.project)
        self.assertEqual(result["lifecycle_status"], "NEEDS_INDEPENDENT_REVIEW")
        self.assertFalse(result["accepted"])

    def test_complete_evidence_review_and_challenge_pass(self) -> None:
        lock = self.freeze()
        self.add_artifact_evidence(lock)
        contract = loop.load_json(loop.contract_path(self.project))
        self.add_passing_review(contract, lock)
        result = loop.policy_gate(self.project)
        self.assertEqual(result["lifecycle_status"], "INDEPENDENTLY_VERIFIED", result)
        self.assertEqual(result["candidate_status"], "CANDIDATE_PASS")
        self.assertTrue(result["accepted"])

    def test_historical_and_nonpassing_records_do_not_poison_current_pass(self) -> None:
        lock = self.freeze()
        self.add_artifact_evidence(lock)
        ledger = loop.ledger_path(self.project)
        records = [json.loads(line) for line in ledger.read_text(encoding="utf-8").splitlines()]
        historical = dict(records[0], record_id="EV-HIST", contract_hash="old-contract")
        failed = dict(records[0], record_id="EV-FAIL", result="FAIL")
        with ledger.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(historical) + "\n")
            handle.write(json.dumps(failed) + "\n")

        contract = loop.load_json(loop.contract_path(self.project))
        coverage = loop.evaluate_evidence_coverage(self.project, contract, lock)

        self.assertTrue(coverage["complete"], coverage)
        self.assertEqual([item["record_id"] for item in coverage["historical_records"]], ["EV-HIST"])
        self.assertEqual([item["record_id"] for item in coverage["nonpassing_records"]], ["EV-FAIL"])
        self.assertEqual(coverage["invalid_records"], [])

        missing_hash = {key: value for key, value in records[0].items() if key != "contract_hash"}
        missing_hash["record_id"] = "EV-NO-HASH"
        missing_result = {key: value for key, value in records[0].items() if key != "result"}
        missing_result["record_id"] = "EV-NO-RESULT"
        with ledger.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(missing_hash) + "\n")
            handle.write(json.dumps(missing_result) + "\n")

        coverage = loop.evaluate_evidence_coverage(self.project, contract, lock)
        self.assertFalse(coverage["complete"], coverage)
        self.assertEqual(
            [item["record_id"] for item in coverage["invalid_records"]],
            ["EV-NO-HASH", "EV-NO-RESULT"],
        )

    def test_review_becomes_stale_after_workspace_change(self) -> None:
        lock = self.freeze()
        self.add_artifact_evidence(lock)
        contract = loop.load_json(loop.contract_path(self.project))
        self.add_passing_review(contract, lock)
        (self.project / "implementation.txt").write_text("changed after review\n", encoding="utf-8")
        result = loop.policy_gate(self.project)
        self.assertEqual(result["lifecycle_status"], "REVIEW_FAILED")
        self.assertTrue(any("workspace_fingerprint" in reason for reason in result["reasons"]))

    def test_policy_drift_invalidates_contract_lock(self) -> None:
        self.freeze()
        policy = self.project / ".codex" / "runtime" / "acceptance.md"
        policy.write_text(policy.read_text(encoding="utf-8") + "\nweakened\n", encoding="utf-8")
        status = loop.contract_status(self.project)
        self.assertFalse(status["ready"])
        self.assertIn("POLICY_DRIFT", status["errors"])

    def test_high_risk_candidate_requires_human(self) -> None:
        lock = self.freeze(risk="L3")
        self.add_artifact_evidence(lock)
        contract = loop.load_json(loop.contract_path(self.project))
        self.add_passing_review(contract, lock)
        result = loop.policy_gate(self.project)
        self.assertEqual(result["lifecycle_status"], "NEEDS_HUMAN")
        self.assertFalse(result["accepted"])

    def test_changed_evidence_artifact_invalidates_coverage(self) -> None:
        lock = self.freeze()
        self.add_artifact_evidence(lock)
        artifact = self.project / ".loop" / "evidence" / "SCN-EDGE.txt"
        artifact.write_text("changed after observation\n", encoding="utf-8")
        contract = loop.load_json(loop.contract_path(self.project))
        coverage = loop.evaluate_evidence_coverage(self.project, contract, lock)
        self.assertFalse(coverage["complete"])
        self.assertTrue(any("changed after observation" in item["reason"] for item in coverage["invalid_records"]))

    def rewrite_review(self, mutate) -> None:
        receipt_path = next((self.project / ".loop" / "reviews").glob("*.receipt.json"))
        receipt = loop.load_json(receipt_path)
        review_path = self.project / receipt["review_file"]
        review = loop.load_json(review_path)
        mutate(review)
        loop.write_json(review_path, review)
        receipt["review_sha256"] = loop.sha256_file(review_path)
        loop.write_json(receipt_path, receipt)

    def test_gate_rejects_review_pass_without_bound_evidence(self) -> None:
        lock = self.freeze()
        self.add_artifact_evidence(lock)
        contract = loop.load_json(loop.contract_path(self.project))
        self.add_passing_review(contract, lock)
        self.rewrite_review(lambda review: review["claims"][0].update({"evidence_refs": ["README.md"]}))
        result = loop.policy_gate(self.project)
        self.assertEqual(result["lifecycle_status"], "REVIEW_FAILED")
        self.assertTrue(any("not bound to valid evidence" in reason for reason in result["reasons"]))

    def test_gate_rejects_passing_challenge_without_bound_evidence(self) -> None:
        lock = self.freeze()
        self.add_artifact_evidence(lock)
        contract = loop.load_json(loop.contract_path(self.project))
        self.add_passing_review(contract, lock)
        self.rewrite_review(
            lambda review: review["challenge"]["cases"][0].update({"evidence_refs": ["README.md"]})
        )
        result = loop.policy_gate(self.project)
        self.assertEqual(result["lifecycle_status"], "REVIEW_FAILED")
        self.assertTrue(any("passing challenge" in reason for reason in result["reasons"]))

    def test_gate_rejects_unresolved_review_uncertainty(self) -> None:
        lock = self.freeze()
        self.add_artifact_evidence(lock)
        contract = loop.load_json(loop.contract_path(self.project))
        self.add_passing_review(contract, lock)
        self.rewrite_review(lambda review: review.update({"remaining_uncertainty": ["Visual state not inspected."]}))
        result = loop.policy_gate(self.project)
        self.assertEqual(result["lifecycle_status"], "REVIEW_FAILED")
        self.assertIn("independent review contains unresolved uncertainty", result["reasons"])

    def test_ledger_rejects_evidence_without_direct_marker(self) -> None:
        lock = self.freeze()
        self.add_artifact_evidence(lock)
        ledger = loop.ledger_path(self.project)
        records = [json.loads(line) for line in ledger.read_text(encoding="utf-8").splitlines()]
        records[0].pop("direct")
        ledger.write_text("\n".join(json.dumps(item) for item in records) + "\n", encoding="utf-8")
        contract = loop.load_json(loop.contract_path(self.project))
        coverage = loop.evaluate_evidence_coverage(self.project, contract, lock)
        self.assertFalse(coverage["complete"])
        self.assertTrue(any("direct" in item["reason"] for item in coverage["invalid_records"]))

    def test_dual_review_requires_both_tracks_and_autonomously_approves_risk_gate(self) -> None:
        lock = self.freeze(risk="L3")
        self.add_artifact_evidence(lock)
        constitution = self.project / ".looploop" / "CONSTITUTION.md"
        constitution.parent.mkdir()
        constitution.write_text("# Project Constitution\n\nreview_standard: dual_blind\n", encoding="utf-8")
        contract = loop.load_json(loop.contract_path(self.project))
        self.add_passing_review(contract, lock, "contract")
        missing = loop.policy_gate(self.project)
        self.assertEqual(missing["lifecycle_status"], "NEEDS_INDEPENDENT_REVIEW")
        self.add_passing_review(contract, lock, "adversarial")
        result = loop.policy_gate(self.project)
        self.assertEqual(result["lifecycle_status"], "INDEPENDENTLY_VERIFIED", result)
        self.assertEqual(result["evidence"]["human_gate"], "AUTONOMOUSLY_APPROVED")

    def central_home(self) -> Path:
        home = self.project / "central"
        (home / "policies").mkdir(parents=True)
        (home / "CONSTITUTION.md").write_text("# Orchestrator Constitution\n", encoding="utf-8")
        (home / "POLICY.md").write_text("# Policy Index\n", encoding="utf-8")
        (home / "policies" / "evidence.md").write_text("# Evidence Policy\n", encoding="utf-8")
        return home

    def registry_entry(self) -> dict:
        return {
            "id": "test_project",
            "name": "Test Project",
            "root": str(self.project),
            "project_goal": "Deliver the verified observable test artifact.",
            "constitution": ".looploop/CONSTITUTION.md",
            "state": ".loop/STATE.md",
        }

    def test_registry_rejects_transient_project_fields(self) -> None:
        home = self.central_home()
        entry = self.registry_entry()
        entry["current_goal"] = "must not live in registry"
        loop.write_json(home / "PROJECT_REGISTRY.yaml", {"schema_version": 1, "projects": [entry]})
        result = loop.registry_check_data(home)
        self.assertFalse(result["valid"])
        self.assertTrue(any("forbidden or transient" in item for item in result["errors"]))

    def test_patrol_uses_light_check_only_for_unchanged_active_worker(self) -> None:
        home = self.central_home()
        loop.write_json(home / "PROJECT_REGISTRY.yaml", {"schema_version": 1, "projects": [self.registry_entry()]})
        loop.write_json(
            home / "runtime" / "thread-map.json",
            {
                "projects": {
                    "test_project": {
                        "current_source_thread_id": "thread-1",
                        "worker_status": "active",
                    }
                }
            },
        )
        self.assertEqual(loop.patrol(home, shadow=True), 0)
        first = loop.load_json(home / "runtime" / "patrol-state.json")
        self.assertEqual(first["projects"]["test_project"]["action"], "REPAIR_GOVERNANCE")
        (self.project / ".looploop").mkdir(exist_ok=True)
        (self.project / ".looploop" / "CONSTITUTION.md").write_text("review_standard: dual_blind\n", encoding="utf-8")
        (self.project / ".looploop" / "project-completion-plan.md").write_text("PLAN_READY\n", encoding="utf-8")
        self.assertEqual(loop.patrol(home, shadow=True), 0)
        self.assertEqual(loop.patrol(home, shadow=True), 0)
        receipts = sorted((home / "ledger").glob("patrol-*.json"))
        latest = loop.load_json(receipts[-1])
        self.assertEqual(latest["decisions"][0]["mode"], "LIGHT_CHECK")

    def test_plan_status_ignores_explanatory_status_mentions(self) -> None:
        project = self.project / "plan-status"
        (project / ".loop").mkdir(parents=True)
        (project / ".looploop").mkdir(parents=True)
        (project / ".loop" / "STATE.md").write_text(
            "# State\n\nStatus is pending; not `PLAN_BLOCKED`; not accepted.\n",
            encoding="utf-8",
        )
        (project / ".loop" / "PLAN.md").write_text("# Plan\n", encoding="utf-8")
        (project / ".looploop" / "project-completion-plan.md").write_text(
            "计划状态：`PLAN_READY`\n\n证据不足时不得记为 `PLAN_BLOCKED`。\n",
            encoding="utf-8",
        )

        self.assertEqual(loop.project_plan_status(project), "PLAN_READY")

    def test_plan_status_treats_candidate_as_needing_repair(self) -> None:
        project = self.project / "candidate-status"
        (project / ".loop").mkdir(parents=True)
        (project / ".looploop").mkdir(parents=True)
        (project / ".loop" / "STATE.md").write_text(
            "plan_status: PLAN_READY_CANDIDATE\n",
            encoding="utf-8",
        )
        (project / ".loop" / "PLAN.md").write_text(
            "status: PLAN_READY\n",
            encoding="utf-8",
        )
        (project / ".looploop" / "project-completion-plan.md").write_text(
            "计划状态：`PLAN_READY`\n",
            encoding="utf-8",
        )

        self.assertEqual(loop.project_plan_status(project), "PLAN_NEEDS_REPAIR")

    def test_windows_reviewer_launcher_prefers_command_shim_over_app_alias(self) -> None:
        def fake_which(name: str) -> str | None:
            return {
                "codex.exe": r"C:\\Program Files\\Codex\\codex.exe",
                "codex.cmd": r"C:\\Users\\test\\codex.cmd",
                "codex": r"C:\\Program Files\\Codex\\codex",
            }.get(name)

        with mock.patch.object(loop.os, "name", "nt"), mock.patch.object(loop.shutil, "which", side_effect=fake_which):
            self.assertEqual(
                loop.codex_command_prefix(),
                [loop.os.environ.get("COMSPEC", "cmd.exe"), "/d", "/s", "/c", r"C:\\Users\\test\\codex.cmd"],
            )

    def test_review_output_schema_types_every_const_and_enum(self) -> None:
        schema = json.loads((ROOT / ".codex" / "runtime" / "review_result.schema.json").read_text(encoding="utf-8"))

        def visit(value: object, path: str = "$") -> list[str]:
            errors: list[str] = []
            if isinstance(value, dict):
                if ("const" in value or "enum" in value) and "type" not in value:
                    errors.append(path)
                for key, child in value.items():
                    errors.extend(visit(child, f"{path}.{key}"))
            elif isinstance(value, list):
                for index, child in enumerate(value):
                    errors.extend(visit(child, f"{path}[{index}]"))
            return errors

        self.assertEqual(visit(schema), [])

    def test_review_output_schema_requires_every_closed_object_property(self) -> None:
        schema = json.loads((ROOT / ".codex" / "runtime" / "review_result.schema.json").read_text(encoding="utf-8"))

        def visit(value: object, path: str = "$") -> list[str]:
            errors: list[str] = []
            if isinstance(value, dict):
                properties = value.get("properties")
                if value.get("type") == "object" and value.get("additionalProperties") is False and isinstance(properties, dict):
                    required = value.get("required")
                    if not isinstance(required, list) or set(required) != set(properties):
                        errors.append(path)
                for key, child in value.items():
                    errors.extend(visit(child, f"{path}.{key}"))
            elif isinstance(value, list):
                for index, child in enumerate(value):
                    errors.extend(visit(child, f"{path}[{index}]"))
            return errors

        self.assertEqual(visit(schema), [])

    def test_review_prompt_requires_machine_bindable_ledger_paths(self) -> None:
        self.freeze()
        context = loop.review_context(self.project, "contract")
        prompt = loop.review_prompt(self.project, context)
        self.assertIn("For every PASS claim", prompt)
        self.assertIn("exact project-relative artifact path", prompt)
        self.assertIn("For every PASS challenge case", prompt)
        self.assertIn("record IDs", prompt)

    def test_review_command_uses_monitored_external_scratch(self) -> None:
        scratch = self.project.parent / "reviewer-scratch" / "review-test"
        command = loop.review_exec_command(
            ["codex"],
            self.project / ".codex" / "runtime" / "review_result.schema.json",
            scratch / "output.json",
            scratch,
        )

        self.assertEqual(command[1:4], ["exec", "--sandbox", "danger-full-access"])
        self.assertIn("--skip-git-repo-check", command)
        self.assertNotIn("--add-dir", command)
        self.assertNotIn(str(self.project), command)

    def test_review_mutation_guard_rejects_project_change(self) -> None:
        lock = self.freeze()
        context = loop.review_context(self.project, "contract")
        self.assertEqual(loop.review_mutation_guard(self.project, context)["contract_hash"], lock["contract_hash"])
        (self.project / "README.md").write_text("# Mutated\n", encoding="utf-8")
        with self.assertRaises(loop.GateError):
            loop.review_mutation_guard(self.project, context)

    def test_reviewer_scratch_parent_is_outside_project(self) -> None:
        scratch_root = self.project.parent / "central-review-scratch"
        with mock.patch.dict(loop.os.environ, {"LOOP_REVIEW_SCRATCH_ROOT": str(scratch_root)}):
            parent = loop.reviewer_scratch_parent(self.project)
        self.assertNotEqual(parent, self.project.resolve())
        self.assertNotIn(self.project.resolve(), parent.parents)

    def test_reviewer_scratch_parent_rejects_project_local_override(self) -> None:
        scratch_root = self.project / ".loop" / "reviewer-tmp"
        with mock.patch.dict(loop.os.environ, {"LOOP_REVIEW_SCRATCH_ROOT": str(scratch_root)}):
            with self.assertRaises(loop.GateError):
                loop.reviewer_scratch_parent(self.project)


if __name__ == "__main__":
    unittest.main()
