"""Durable append-only authority event storage."""

import os
from pathlib import Path
from threading import Lock
from core.storage_lock import exclusive_file_lock
from .models import AuthorityEvent


class CorruptEventLog(RuntimeError):
    pass


class AuthorityEventLog:
    def __init__(self, path: str):
        self.path = Path(path)
        self._lock = Lock()

    def append(self, event: AuthorityEvent) -> None:
        with self._lock:
            with exclusive_file_lock(self.path):
                existing_ids = {item.event_id for item in self.read_all()}
                if event.event_id in existing_ids:
                    raise ValueError(f"duplicate event_id: {event.event_id}")
                self.path.parent.mkdir(parents=True, exist_ok=True)
                with self.path.open("a", encoding="utf-8") as handle:
                    handle.write(event.to_json() + "\n")
                    handle.flush()
                    os.fsync(handle.fileno())

    def read_all(self) -> list[AuthorityEvent]:
        if not self.path.exists():
            return []
        events = []
        for line_number, line in enumerate(
            self.path.read_text(encoding="utf-8").splitlines(), start=1
        ):
            if not line.strip():
                continue
            try:
                events.append(AuthorityEvent.from_json(line))
            except (TypeError, ValueError) as exc:
                raise CorruptEventLog(
                    f"invalid authority event at line {line_number}"
                ) from exc
        return events
