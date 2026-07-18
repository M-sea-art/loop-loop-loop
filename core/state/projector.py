"""Deterministic projection layer.

Authority events are the source of truth. Human-readable state files are
projections and must never become authoritative inputs.
"""

from dataclasses import dataclass
from typing import Iterable, Dict, Any


@dataclass
class ProjectedState:
    goal_id: str
    status: str = "DRAFT"
    last_event_id: str | None = None


class StateProjector:
    """Build runtime state from authority events only."""

    def project(self, events: Iterable[Dict[str, Any]]) -> ProjectedState:
        state = ProjectedState(goal_id="unknown")

        for event in events:
            state.goal_id = event.get("goal_id", state.goal_id)
            state.last_event_id = event.get("event_id")

            if event.get("action") == "GOAL_STATUS_CHANGED":
                state.status = event.get("to", state.status)

        return state
