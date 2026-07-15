from __future__ import annotations

import importlib.util
import json
import shutil
import tempfile
import unittest
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

    def test_install_preserves_existing_codex_config(self) -> None:
        config = self.project / ".codex" / "config.toml"
        config.write_text(
            'model = "codex-default"\nsandbox_mode = "workspace-write"\n',
            encoding="utf-8",
        )
        before = config.read_bytes()

        loop.install(self.project)

        self.assertEqual(config.read_bytes(), before)
        self.assertTrue(
            (self.project / ".codex" / "runtime" / "adaptive-execution.md").is_file()
        )

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

    def add_passing_review(self, contract: dict, lock: dict) -> None:
        context = loop.review_context(self.project)
        review = {
            "review_context_id": context["review_context_id"],
            "reviewer_role": "independent_reviewer",
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
        review_file = self.project / ".loop" / "reviews" / "review-test.json"
        loop.write_json(review_file, review)
        receipt = {
            "receipt_version": 1,
            "created_at": loop.now_iso(),
            "mode": "separate_codex_exec_read_only",
            "review_file": str(review_file.relative_to(self.project)),
            "review_sha256": loop.sha256_file(review_file),
            "review_context": context,
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


if __name__ == "__main__":
    unittest.main()
