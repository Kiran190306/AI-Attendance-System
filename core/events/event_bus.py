from __future__ import annotations

import threading
import queue
import logging
from typing import Any, Callable, Dict

logger = logging.getLogger(__name__)


class EventBus:
    """Simple publish/subscribe event queue used to decouple cameras from the
    attendance service.

    Camera threads publish recognition events which are dispatched to
    registered listeners on a separate thread.  All events are also logged for
    later debugging.
    """

    def __init__(self) -> None:
        self._queue: queue.Queue[Dict[str, Any]] = queue.Queue()
        self._listeners: list[Callable[[Dict[str, Any]], None]] = []
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._running = False
        self.log_file = "logs/recognition_events.log"
        # ensure log folder exists
        import os
        os.makedirs("logs", exist_ok=True)

    def start(self) -> None:
        if not self._running:
            self._running = True
            self._thread.start()
            logger.info("event bus started")

    def stop(self) -> None:
        self._running = False
        # wake up thread
        self._queue.put(None)
        self._thread.join()
        logger.info("event bus stopped")

    def publish(self, event: Dict[str, Any]) -> None:
        """Queue a new event for delivery.

        The event is written to the recognition_events.log file as JSON on
        a single line.
        """
        # add timestamp if not provided
        if "timestamp" not in event:
            from datetime import datetime
            event["timestamp"] = datetime.now().isoformat()
        self._queue.put(event)
        try:
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(f"{event}\n")
        except Exception:  # logging should never crash
            logger.warning("failed to write to recognition log")
        logger.debug("event published: %s", event)

    def register(self, callback: Callable[[Dict[str, Any]], None]) -> None:
        self._listeners.append(callback)

    def _run(self) -> None:
        while self._running:
            try:
                event = self._queue.get(timeout=1)
            except queue.Empty:
                continue
            if event is None:
                break
            for cb in self._listeners:
                try:
                    cb(event)
                except Exception as exc:
                    logger.exception("listener raised: %s", exc)
