"""Acceptance tests for Runtime Reliability v1 scenario registration."""

from examples.runtime_reliability.e2e_acceptance.run_acceptance import run_acceptance


def test_acceptance_scenarios_registered():
    result = run_acceptance()

    assert result["status"] == "READY_FOR_RUNTIME_INTEGRATION"
    assert "success_case" in result["scenarios"]
    assert "revoke_case" in result["scenarios"]
    assert "no_progress_case" in result["scenarios"]
    assert "writer_conflict_case" in result["scenarios"]
