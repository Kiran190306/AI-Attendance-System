from __future__ import annotations

import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class AnomalyDetector:
    """Track individual positions over time to flag unusual behavior.

    For demonstration we mark repeated entries/exits or very fast motion as
    suspicious.  In a production system this would be replaced by a learned
    model or more sophisticated rules.
    """

    def __init__(self):
        # simple history: person_id -> last positions (x,y) and frame count
        self.history: Dict[int, Dict] = {}
        self.frame_index = 0

    def analyze(self, person_id: Optional[int], bbox: tuple[int, int, int, int]) -> float:
        """Return suspicious confidence (0.0-1.0)."""
        self.frame_index += 1
        if person_id is None:
            return 0.0

        x1, y1, x2, y2 = bbox
        cx = (x1 + x2) / 2
        cy = (y1 + y2) / 2

        rec = self.history.get(person_id)
        if rec is None:
            self.history[person_id] = {"pos": (cx, cy), "last_frame": self.frame_index, "visits": 1}
            return 0.0

        dx = cx - rec["pos"][0]
        dy = cy - rec["pos"][1]
        dist = (dx * dx + dy * dy) ** 0.5
        rec["pos"] = (cx, cy)
        if self.frame_index - rec["last_frame"] < 10 and dist < 5:
            # likely hovering/loitering
            rec["visits"] += 1
        rec["last_frame"] = self.frame_index
        # mark suspicious if many short visits
        conf = 1.0 if rec["visits"] > 5 else 0.0
        logger.debug("anomaly pid=%s visits=%d conf=%.1f", person_id, rec["visits"], conf)
        return conf
