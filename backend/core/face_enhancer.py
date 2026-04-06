"""Image enhancement utilities for low-resolution faces."""
from __future__ import annotations

import cv2
import numpy as np


def enhance_face(face: np.ndarray) -> np.ndarray:
    """Return an enhanced version of the face crop.

    Applies a simple sharpening filter and upscales very small faces.
    """
    h, w = face.shape[:2]
    # upscale if too small
    if max(h, w) < 64:
        face = cv2.resize(face, (w * 2, h * 2), interpolation=cv2.INTER_CUBIC)
    # sharpening kernel
    kernel = np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]])
    face = cv2.filter2D(face, -1, kernel)
    return face
