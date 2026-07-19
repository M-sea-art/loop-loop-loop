"""Runtime progress truth model.

Only observable goal movement counts as progress.
"""

from dataclasses import dataclass, field

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


@dataclass(frozen=True)
class ProgressInvariant:
    signals: set[str] = field(default_factory=set)

    def has_progress(self) -> bool:
        return is_real_progress(self.signals)
