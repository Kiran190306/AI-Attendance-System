from __future__ import annotations

import numpy as np
import cv2


class HeatmapGenerator:
    """Accumulates points over time to create a heatmap overlay.

    Every detected person adds the centroid of their bounding box to an
    accumulation matrix which is then colorized.
    """

    def __init__(self, decay: float = 0.95) -> None:
        self.decay = decay
        self.accum: np.ndarray | None = None

    def update(self, frame: np.ndarray, boxes: list[tuple[int, int, int, int]]) -> None:
        h, w = frame.shape[:2]
        if self.accum is None:
            self.accum = np.zeros((h, w), dtype=np.float32)

        # decay previous heatmap
        self.accum *= self.decay

        for (x1, y1, x2, y2) in boxes:
            cx = int((x1 + x2) / 2)
            cy = int((y1 + y2) / 2)
            if 0 <= cx < w and 0 <= cy < h:
                self.accum[cy, cx] += 1.0

    def overlay(self, frame: np.ndarray) -> np.ndarray | None:
        if self.accum is None:
            return None
        # normalize and apply colormap
        im = cv2.normalize(self.accum, None, 0, 255, cv2.NORM_MINMAX)
        im = im.astype(np.uint8)
        heat = cv2.applyColorMap(im, cv2.COLORMAP_JET)
        heat = cv2.resize(heat, (frame.shape[1], frame.shape[0]))
        return heat
