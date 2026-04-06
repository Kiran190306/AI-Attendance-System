import logging
from datetime import datetime
from pathlib import Path
from typing import Tuple, Optional

import cv2
import numpy as np

from ..config import DATASET_PATH

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# dataset helpers
# ---------------------------------------------------------------------------

def ensure_dataset_exists(dataset_path: Path) -> None:
    if not dataset_path.exists() or not dataset_path.is_dir():
        raise FileNotFoundError(f"Dataset directory does not exist: {dataset_path}")


def normalize_student_name(name: str) -> str:
    if not isinstance(name, str):
        return ""
    return " ".join(name.strip().title().split())


# ---------------------------------------------------------------------------
# camera / UI helpers
# ---------------------------------------------------------------------------

def open_camera(index: int = 0) -> cv2.VideoCapture:
    cap = cv2.VideoCapture(index)
    if not cap.isOpened():
        raise RuntimeError(f"Cannot open camera at index {index}")
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
    return cap


def draw_box_with_label(
    frame: np.ndarray,
    x1: int,
    y1: int,
    x2: int,
    y2: int,
    label: str,
    color: Tuple[int, int, int],
    thickness: int = 2,
) -> None:
    cv2.rectangle(frame, (x1, y1), (x2, y2), color, thickness)
    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 0.6
    font_thick = 1
    (text_width, text_height), baseline = cv2.getTextSize(label, font, font_scale, font_thick)
    cv2.rectangle(
        frame,
        (x1, y1 - text_height - 8),
        (x1 + text_width + 8, y1),
        color,
        -1,
    )
    cv2.putText(
        frame,
        label,
        (x1 + 4, y1 - 4),
        font,
        font_scale,
        (255, 255, 255),
        font_thick,
    )


def draw_status_badge(
    frame: np.ndarray,
    status: str,
    x: int,
    y: int,
    color: Tuple[int, int, int],
) -> None:
    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 0.5
    font_thick = 1
    (text_width, text_height), baseline = cv2.getTextSize(status, font, font_scale, font_thick)
    cv2.rectangle(
        frame,
        (x - 4, y - text_height - 4),
        (x + text_width + 4, y + baseline + 4),
        color,
        -1,
    )
    cv2.putText(
        frame,
        status,
        (x, y),
        font,
        font_scale,
        (0, 0, 0),
        font_thick,
    )


def draw_info_panel(
    frame: np.ndarray,
    title: str,
    info_lines: list[str],
    position: str = "top-left",
    bg_color: Tuple[int, int, int] = (40, 40, 40),
    text_color: Tuple[int, int, int] = (200, 200, 200),
    margin: int = 10,
) -> None:
    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 0.5
    font_thick = 1
    line_height = 20
    h, w = frame.shape[:2]
    all_lines = [title] + info_lines
    panel_width = max(len(line) * 8 for line in all_lines) + 20
    panel_height = len(all_lines) * line_height + 10
    if position == "top-left":
        x, y = margin, margin
    elif position == "top-right":
        x, y = w - panel_width - margin, margin
    elif position == "bottom-left":
        x, y = margin, h - panel_height - margin
    else:
        x, y = w - panel_width - margin, h - panel_height - margin
    cv2.rectangle(frame, (x, y), (x + panel_width, y + panel_height), bg_color, -1)
    cv2.putText(
        frame,
        title,
        (x + 10, y + 18),
        font,
        font_scale + 0.1,
        text_color,
        font_thick + 1,
    )
    for i, line in enumerate(info_lines):
        cv2.putText(
            frame,
            line,
            (x + 10, y + 18 + (i + 1) * line_height),
            font,
            font_scale,
            text_color,
            font_thick,
        )


def draw_instruction_text(
    frame: np.ndarray,
    text: str,
    position: str = "bottom",
) -> None:
    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 0.5
    font_thick = 1
    color = (150, 150, 150)
    h, w = frame.shape[:2]
    (text_width, text_height), baseline = cv2.getTextSize(text, font, font_scale, font_thick)
    if position == "top":
        x = (w - text_width) // 2
        y = 20
    else:
        x = (w - text_width) // 2
        y = h - 10
    cv2.putText(frame, text, (x, y), font, font_scale, color, font_thick)
