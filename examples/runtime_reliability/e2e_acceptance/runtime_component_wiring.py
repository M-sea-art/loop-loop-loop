"""Runtime component wiring acceptance.

This module defines the intended execution path after Runtime Reliability v1:

Goal
 -> RuntimeContext
 -> Authority Pipeline
 -> Evidence
 -> Judge
 -> Gate

The scaffold keeps integration boundaries explicit before replacing each step
with concrete runtime implementations.
"""

import sys
from pathlib import Path
from tempfile import TemporaryDirectory

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from examples.runtime_reliability.scenarios import run_success_case


class RuntimeResult:
    def __init__(self, state: str, evidence_verified: bool):
        self.state = state
        self.evidence_verified = evidence_verified


def run_component_wiring(
    goal_id: str, workspace: str | Path | None = None
) -> RuntimeResult:
    """Execute the production reliability components as one chain."""
    if not goal_id:
        raise ValueError("goal_id required")
    if workspace is not None:
        result = run_success_case(workspace)
        return RuntimeResult(result.status, bool(result.evidence))
    with TemporaryDirectory() as directory:
        result = run_success_case(directory)
        return RuntimeResult(result.status, bool(result.evidence))
