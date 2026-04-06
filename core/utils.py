import logging
from pathlib import Path
from datetime import datetime
from typing import Optional, Tuple

import cv2
import numpy as np


# ---------------------------------------------------------------------------
# logging helpers
# ---------------------------------------------------------------------------

def setup_logging(level: Optional[str] = None) -> None:
    """Configure the root logger using the settings from :mod:`config`."""
    lvl = level or logging.getLogger().level
    logging.basicConfig(level=lvl, format="%(asctime)s - %(levelname)s - %(name)s - %(message)s")


# ---------------------------------------------------------------------------
# general helpers
# ---------------------------------------------------------------------------

def normalize_student_name(name: str) -> str:
    """Normalize a student name for storage/comparison.

    Strips whitespace, collapses multiple spaces and title-cases the string.
    Used by ``AttendanceService`` and the database modules to keep names
    consistent.
    """
    if not isinstance(name, str):
        return ""
    return " ".join(name.strip().title().split())


def ensure_dataset_exists(dataset_path: Path) -> None:
    """Raise :class:`FileNotFoundError` if dataset directory is missing."""
    if not dataset_path.exists() or not dataset_path.is_dir():
        raise FileNotFoundError(f"Dataset directory does not exist: {dataset_path}")


def open_camera(index: int = 0) -> cv2.VideoCapture:
    """Return an opened :class:`cv2.VideoCapture` or raise ``RuntimeError``."""
    cap = cv2.VideoCapture(index)
    if not cap.isOpened():
        raise RuntimeError(f"Cannot open camera at index {index}")
    # optional: set reasonable defaults
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
    return cap


# simple date helpers

def today_str() -> str:
    return datetime.now().strftime("%Y-%m-%d")


# ---------------------------------------------------------------------------
# UI overlay helpers (OpenCV)
# ---------------------------------------------------------------------------

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
    """Draw a bounding box with label text on frame.
    
    Args:
        frame: Input frame (modified in-place)
        x1, y1, x2, y2: Bounding box coordinates
        label: Text to display above box
        color: BGR color tuple
        thickness: Line thickness
    """
    cv2.rectangle(frame, (x1, y1), (x2, y2), color, thickness)
    
    # Draw label background
    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 0.6
    font_thick = 1
    
    (text_width, text_height), baseline = cv2.getTextSize(label, font, font_scale, font_thick)
    
    # Background rectangle for text
    cv2.rectangle(
        frame,
        (x1, y1 - text_height - 8),
        (x1 + text_width + 8, y1),
        color,
        -1,
    )
    
    # Text
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
    """Draw a status badge (e.g., '✓ MARKED' or '? UNKNOWN').
    
    Args:
        frame: Input frame (modified in-place)
        status: Status text
        x, y: Position
        color: BGR color
    """
    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 0.5
    font_thick = 1
    
    (text_width, text_height), baseline = cv2.getTextSize(status, font, font_scale, font_thick)
    
    # Background
    cv2.rectangle(
        frame,
        (x - 4, y - text_height - 4),
        (x + text_width + 4, y + baseline + 4),
        color,
        -1,
    )
    
    # Text
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
    """Draw an information panel on frame.
    
    Args:
        frame: Input frame (modified in-place)
        title: Panel title
        info_lines: List of info strings
        position: 'top-left', 'top-right', 'bottom-left', 'bottom-right'
        bg_color: Background BGR color
        text_color: Text BGR color
        margin: Margin from edge
    """
    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 0.5
    font_thick = 1
    line_height = 20
    
    h, w = frame.shape[:2]
    
    # Calculate panel size
    all_lines = [title] + info_lines
    panel_width = max(len(line) * 8 for line in all_lines) + 20
    panel_height = len(all_lines) * line_height + 10
    
    # Determine position
    if position == "top-left":
        x, y = margin, margin
    elif position == "top-right":
        x, y = w - panel_width - margin, margin
    elif position == "bottom-left":
        x, y = margin, h - panel_height - margin
    else:  # bottom-right
        x, y = w - panel_width - margin, h - panel_height - margin
    
    # Draw background
    cv2.rectangle(frame, (x, y), (x + panel_width, y + panel_height), bg_color, -1)
    
    # Draw title
    cv2.putText(
        frame,
        title,
        (x + 10, y + 18),
        font,
        font_scale + 0.1,
        text_color,
        font_thick + 1,
    )
    
    # Draw info lines
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
    """Draw instruction text on frame.
    
    Args:
        frame: Input frame (modified in-place)
        text: Instruction text
        position: 'top' or 'bottom'
    """
    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 0.5
    font_thick = 1
    color = (150, 150, 150)
    
    h, w = frame.shape[:2]
    (text_width, text_height), baseline = cv2.getTextSize(text, font, font_scale, font_thick)
    
    if position == "top":
        x = (w - text_width) // 2
        y = 20
    else:  # bottom
        x = (w - text_width) // 2
        y = h - 10
    
    cv2.putText(frame, text, (x, y), font, font_scale, color, font_thick)
