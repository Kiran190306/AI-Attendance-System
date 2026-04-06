from __future__ import annotations

import time
from typing import List, Tuple, Dict, Optional


class MovementTracker:
    """Simple bbox tracker to compute entry/exit rates and dwell time.

    A naive implementation that matches boxes by centroid proximity.
    """

    def __init__(self, max_distance: float = 50.0) -> None:
        # next internal id
        self._next = 1
        # id -> (centroid, first_seen, last_seen)
        self._tracks: Dict[int, Tuple[Tuple[int, int], float, float]] = {}
        # history of dwell times
        self._dwell_times: List[float] = []
        self.max_distance = max_distance

    def _centroid(self, box: Tuple[int, int, int, int]) -> Tuple[int, int]:
        x1, y1, x2, y2 = box
        return ((x1 + x2) // 2, (y1 + y2) // 2)

    def update(self, boxes: List[Tuple[int, int, int, int]]) -> None:
        now = time.time()
        new_centroids = [self._centroid(b) for b in boxes]
        used_ids = set()

        # attempt to match existing tracks
        for cid in list(self._tracks.keys()):
            cent, first, last = self._tracks[cid]
            # find nearest new centroid
            best_idx = None
            best_dist = None
            for idx, nc in enumerate(new_centroids):
                if idx in used_ids:
                    continue
                dist = ((cent[0] - nc[0]) ** 2 + (cent[1] - nc[1]) ** 2) ** 0.5
                if best_dist is None or dist < best_dist:
                    best_dist = dist
                    best_idx = idx
            if best_idx is not None and best_dist is not None and best_dist < self.max_distance:
                # update track
                nc = new_centroids[best_idx]
                self._tracks[cid] = (nc, first, now)
                used_ids.add(best_idx)
            else:
                # track disappeared
                # record dwell time
                self._dwell_times.append(last - first)
                del self._tracks[cid]

        # remaining centroids create new tracks
        for idx, nc in enumerate(new_centroids):
            if idx in used_ids:
                continue
            self._tracks[self._next] = (nc, now, now)
            self._next += 1

    @property
    def entry_rate(self) -> float:
        # simple approximation: total entries per minute
        if not self._tracks:
            return 0.0
        oldest = min(v[1] for v in self._tracks.values())
        duration = time.time() - oldest
        if duration <= 0:
            return 0.0
        return len(self._tracks) / (duration / 60.0)

    @property
    def exit_rate(self) -> float:
        # of completed tracks per minute (based on dwell history)
        if not self._dwell_times:
            return 0.0
        # assume timeframe of last track
        # this is a stub; proper implementation would count by timestamp
        return len(self._dwell_times)

    @property
    def avg_dwell(self) -> float:
        if not self._dwell_times:
            return 0.0
        return sum(self._dwell_times) / len(self._dwell_times)
