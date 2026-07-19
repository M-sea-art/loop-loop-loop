"""Runtime Reliability v1 end-to-end acceptance entry point."""

from examples.runtime_reliability.run_all_scenarios import run


def run_acceptance() -> dict:
    results = run()
    statuses = {name: result.status for name, result in results.items()}
    return {
        "scenarios": statuses,
        "status": "VERIFIED_COMPLETE"
        if statuses
        == {
            "success_case": "VERIFIED_COMPLETE",
            "revoke_case": "VERIFIED_STOPPED",
            "no_progress_case": "STOPPED_NO_PROGRESS",
            "writer_conflict_case": "SECOND_WRITER_REJECTED",
        }
        else "VERIFICATION_FAILED",
    }


if __name__ == "__main__":
    print(run_acceptance())
