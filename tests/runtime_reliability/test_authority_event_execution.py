from examples.runtime_reliability.e2e_acceptance.authority_event_execution import execute_goal_event


def test_authority_event_execution_records_event():
    result = execute_goal_event("goal-demo")
    assert result["event_recorded"] is True
    assert result["authority_source"] == "event_log"
