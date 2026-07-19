"""Validate runtime write ownership."""

from .models import WriterLease


class LeaseViolation(Exception):
    pass


READ_ONLY_ACTORS = {
    "observer",
    "reviewer",
    "patrol",
}


def validate_writer(lease: WriterLease, actor: str) -> None:
    if actor in READ_ONLY_ACTORS:
        raise LeaseViolation(f"{actor} cannot mutate runtime state")

    if not lease.is_owned_by(actor):
        raise LeaseViolation("actor does not own active writer lease")
