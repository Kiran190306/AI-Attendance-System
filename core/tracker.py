from __future__ import annotations

import threading
import time
from typing import Optional


class Tracker:
    """Assigns temporary tracking IDs to recognized individuals across cameras.

    If the same person is seen on a different camera within a configurable time
    window we reuse the previous tracking ID.  The keeper is intentionally
    lightweight and thread-safe.
    """

    def __init__(self, max_idle_seconds: float = 30.0) -> None:
        self._lock = threading.Lock()
        self._next_id = 1
        # name -> (track_id, last_seen_timestamp)
        self._records: dict[str, tuple[int, float]] = {}
        self.max_idle = max_idle_seconds

    def assign(self, name: Optional[str]) -> Optional[int]:
        """Return a tracking ID for ``name`` or ``None`` for unknown people.

        The ID remains stable as long as the person continues to be seen
        within ``max_idle`` seconds; otherwise a new ID is generated.
        """
        if not name:
            return None
        now = time.time()
        with self._lock:
            rec = self._records.get(name)
            if rec is not None:
                ident, last = rec
                if now - last < self.max_idle:
                    # update timestamp and return existing id
                    self._records[name] = (ident, now)
                    return ident
            # new/expired entry
            ident = self._next_id
            self._next_id += 1
            self._records[name] = (ident, now)
            return ident

    def purge_old(self) -> None:
        """Remove records that have been idle for longer than ``max_idle``.

        This can be called periodically from a housekeeping thread if desired.
        """
        now = time.time()
        with self._lock:
            for name in list(self._records.keys()):
                _, last = self._records[name]
                if now - last > self.max_idle:
                    del self._records[name]
