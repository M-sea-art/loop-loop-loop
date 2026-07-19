from examples.runtime_reliability.e2e_acceptance.runtime_component_wiring import run_component_wiring


def test_component_wiring_returns_verified_state():
    result = run_component_wiring("demo-goal")

    assert result.state == "VERIFIED_COMPLETE"
    assert result.evidence_verified is True
