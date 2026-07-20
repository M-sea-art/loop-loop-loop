from examples.runtime_reliability.e2e_acceptance.real_authority_event_path import (
    run_authority_event_path,
)


def test_authority_event_path_records_event():
    result = run_authority_event_path("goal-1")

    assert result.event_recorded is True
    assert result.terminal_state == "VERIFIED_COMPLETE"
