"""Basic reliability pipeline scenario checks."""

from core.runtime.context import RuntimeContext


def test_runtime_context_keeps_authority_scope():
    context = RuntimeContext(
        goal_id="goal-1",
        contract_hash="contract",
        writer_id="executor",
    )

    assert context.goal_id == "goal-1"
    assert context.writer_id == "executor"
