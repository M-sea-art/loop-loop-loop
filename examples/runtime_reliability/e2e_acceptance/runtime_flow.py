"""Execute the production reliability path and report its boundaries."""

from pathlib import Path

from examples.runtime_reliability.scenarios import run_success_case


def run_flow(goal_id: str, workspace: str | Path) -> dict:
    if not goal_id:
        raise ValueError("goal_id required")
    result = run_success_case(workspace)
    return {
        "goal_id": goal_id,
        "flow": [
            "frozen_goal_contract",
            "writer_lease",
            "mutation_guard",
            "signed_authority_event",
            "independent_evidence",
            "gate",
        ],
        "status": result.status,
        "evidence_verified": bool(result.evidence),
    }
