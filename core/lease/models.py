"""Lease primitives for single-writer runtime ownership."""

from dataclasses import dataclass
from dataclasses import asdict


@dataclass
class WriterLease:
    project_id: str
    goal_id: str
    writer: str
    thread_id: str
    contract_hash: str
    acquired_at: str
    expires_at: str

    def is_owned_by(self, actor: str) -> bool:
        return self.writer == actor

    def to_dict(self) -> dict:
        return asdict(self)
