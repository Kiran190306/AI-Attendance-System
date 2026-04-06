"""Helper for validating embeddings against stored student vectors."""
from __future__ import annotations

import numpy as np
from typing import Dict, List, Optional


class EmbeddingValidator:
    def __init__(
        self,
        embeddings_map: Dict[str, List[np.ndarray]],
        threshold: float = 0.6,
    ) -> None:
        # embeddings_map: student_name -> list of reference embeddings
        self.embeddings = embeddings_map
        self.threshold = threshold

    def validate(self, name: str, emb: np.ndarray) -> bool:
        """Return True if embedding is sufficiently similar to stored samples."""
        if name not in self.embeddings:
            # no reference data, trust by default
            return True
        refs = self.embeddings[name]
        if not refs:
            return True
        dists = [np.linalg.norm(emb - r) for r in refs]
        best = min(dists)
        return best <= self.threshold

    def best_distance(self, name: str, emb: np.ndarray) -> Optional[float]:
        """Return best L2 distance or None if no refs."""
        if name not in self.embeddings or not self.embeddings[name]:
            return None
        return float(min(np.linalg.norm(emb - r) for r in self.embeddings[name]))
