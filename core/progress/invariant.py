"""Runtime progress truth model.

Only observable goal movement counts as progress.
"""

VALID_PROGRESS_SIGNALS = {
    "artifact_changed",
    "acceptance_improved",
    "blocker_removed",
    "gate_verified",
}

INVALID_PROGRESS_SIGNALS = {
    "state_updated",
    "report_created",
    "heartbeat",
    "agent_spawned",
}


def is_real_progress(signals: set[str]) -> bool:
    return bool(signals.intersection(VALID_PROGRESS_SIGNALS))
