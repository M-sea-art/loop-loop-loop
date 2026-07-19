"""Acceptance runner contract tests."""

from examples.runtime_reliability.run_all_scenarios import SCENARIOS


def test_all_reliability_scenarios_registered():
    assert set(SCENARIOS) == {
        "success_case",
        "revoke_case",
        "no_progress_case",
        "writer_conflict_case",
    }
