from examples.runtime_reliability.e2e_acceptance.runtime_execution_demo import (
    run_success_case,
)


def test_success_case_reaches_verified_complete():
    result = run_success_case()

    assert result.status == "VERIFIED_COMPLETE"
    assert "evidence_verified" in result.evidence
