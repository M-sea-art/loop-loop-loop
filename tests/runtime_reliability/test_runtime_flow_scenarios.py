"""Acceptance checks for runtime flow scenarios."""

from examples.runtime_reliability.e2e_acceptance.runtime_flow import run_flow


def test_runtime_flow_has_reliability_boundaries():
    result = run_flow("goal-001")

    assert result["flow"] == [
        "runtime_context",
        "mutation_guard",
        "authority_event",
        "evidence",
        "judge",
        "gate",
    ]
    assert result["status"] == "READY_FOR_RUNTIME_WIRING"
