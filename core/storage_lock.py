"""Small cross-platform lock-file primitive for authoritative stores."""

from __future__ import annotations

from contextlib import contextmanager
import json
import os
from pathlib import Path
import socket
import time
import uuid


def _owner_is_alive(lock_path: Path) -> bool:
    """Return whether a well-formed lock belongs to a live local process."""
    try:
        payload = json.loads(lock_path.read_text(encoding="utf-8"))
        pid = int(payload["pid"])
        hostname = str(payload["hostname"])
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError):
        try:
            return time.time() - lock_path.stat().st_mtime < 0.1
        except OSError:
            return False
    if hostname != socket.gethostname():
        return True
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


@contextmanager
def exclusive_file_lock(path: str | Path | None, timeout: float = 1.0):
    if path is None:
        yield
        return
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    lock_path = target.with_suffix(target.suffix + ".lock")
    deadline = time.monotonic() + timeout
    descriptor = None
    token = uuid.uuid4().hex
    while descriptor is None:
        try:
            descriptor = os.open(
                lock_path,
                os.O_CREAT | os.O_EXCL | os.O_WRONLY,
                0o600,
            )
        except FileExistsError:
            if not _owner_is_alive(lock_path):
                try:
                    lock_path.unlink()
                except FileNotFoundError:
                    pass
                continue
            if time.monotonic() >= deadline:
                raise RuntimeError(f"authoritative store is locked: {target}")
            time.sleep(0.01)
    try:
        owner = {
            "pid": os.getpid(),
            "hostname": socket.gethostname(),
            "token": token,
            "created_at": time.time(),
        }
        os.write(descriptor, json.dumps(owner).encode("utf-8"))
        os.fsync(descriptor)
        yield
    finally:
        os.close(descriptor)
        try:
            current = json.loads(lock_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            current = {}
        if current.get("token") == token:
            lock_path.unlink(missing_ok=True)
