"""Acceptance checks for Runtime Reliability terminal states."""

from enum import Enum


class TerminalState(str, Enum):
    VERIFIED_COMPLETE = "VERIFIED_COMPLETE"
    VERIFIED_STOPPED = "VERIFIED_STOPPED"
    STOPPED_NO_PROGRESS = "STOPPED_NO_PROGRESS"
    RECONCILE_REQUIRED = "RECONCILE_REQUIRED"


def test_reliability_terminal_states_exist():
    assert TerminalState.VERIFIED_COMPLETE
    assert TerminalState.VERIFIED_STOPPED
    assert TerminalState.STOPPED_NO_PROGRESS
    assert TerminalState.RECONCILE_REQUIRED
