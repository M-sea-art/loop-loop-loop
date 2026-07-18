"""State reconciliation helpers.

The runtime prefers deterministic repair from authority events instead of
trusting possibly stale projections.
"""

from typing import Dict, Any


class ReconciliationRequired(Exception):
    pass


def compare_projection(projected: Dict[str, Any], observed: Dict[str, Any]) -> bool:
    """Return whether a projection matches expected authority state."""
    return projected == observed


def require_reconciliation(projected: Dict[str, Any], observed: Dict[str, Any]) -> None:
    if not compare_projection(projected, observed):
        raise ReconciliationRequired(
            "Projection drift detected; rebuild from authority events."
        )
