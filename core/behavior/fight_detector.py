from __future__ import annotations

import logging
from typing import Dict

logger = logging.getLogger(__name__)


class FightDetector:
    """Simple heuristics to flag aggressive movements based on pose motion.

    This stub implementation looks for large motion vectors on upper limbs.
    """

    def __init__(self, aggression_threshold: float = 0.7):
        self.threshold = aggression_threshold

    def detect(self, pose_data: Dict[str, any]) -> float:
        """Return aggression confidence (0.0-1.0).

        ``pose_data`` is expected to contain a "motions" dict with landmark
        motion vectors from :class:`PoseAnalyzer`.
        """
        motions = pose_data.get("motions", {})
        # check wrist speed as simple proxy
        left_wrist = motions.get("LEFT_WRIST", (0, 0, 0))
        right_wrist = motions.get("RIGHT_WRIST", (0, 0, 0))
        mag = max(sum(abs(v) for v in left_wrist), sum(abs(v) for v in right_wrist))
        # normalize arbitrarily (real system would calibrate)
        conf = min(1.0, mag * 5)
        logger.debug("fight detector mag=%.3f conf=%.3f", mag, conf)
        return conf
