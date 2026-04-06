from __future__ import annotations

import csv
import logging
from datetime import datetime, date
from pathlib import Path
from typing import List, Optional, Tuple, Set, Dict
from collections import deque

from . import config, utils

logger = logging.getLogger(__name__)


class AttendanceServiceError(Exception):
    """Raised when attendance operations fail."""
    pass


class AttendanceService:
    """Professional CSV-based attendance logger with comprehensive features.
    
    Features:
    - Stores attendance in attendance/attendance.csv
    - Prevents duplicate attendance per student per day (across cameras)
    - Tracks timestamp, camera source and date separately
    - Logs unknown face detections
    - Session statistics tracking
    - Production-grade error handling
    
    CSV format: date,time,name,camera_id,timestamp_iso,confidence
    """

    def __init__(self, csv_path: Path | str = config.ATTENDANCE_CSV) -> None:
        self.csv_path = Path(csv_path)
        self.csv_path.parent.mkdir(parents=True, exist_ok=True)
        
        self._today = date.today().isoformat()
        self._marked: Set[str] = set()  # session-level duplicates today
        self._recent_entries: deque = deque(maxlen=10)  # recent activity
        
        # Session statistics
        self._session_stats = {
            "recognized": 0,
            "unknown": 0,
            "duplicates_prevented": 0,
        }
        
        self._load_existing()
        logger.info("attendance service initialized (csv: %s)", self.csv_path)

    # ------------------------------------------------------------------
    # internal helpers
    # ------------------------------------------------------------------

    def _load_existing(self) -> None:
        """Load today's records to prevent duplicates."""
        if not self.csv_path.exists():
            return
        try:
            with open(self.csv_path, newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                if reader.fieldnames is None:
                    return
                
                for row in reader:
                    if not row.get("date"):
                        continue
                    # Only track today's records
                    if row["date"] == self._today:
                        name = row.get("name", "").lower().strip()
                        if name:
                            self._marked.add(name)
        except Exception as exc:
            logger.warning("failed to load existing attendance: %s", exc)

    def _ensure_csv_headers(self) -> None:
        """Ensure CSV has proper headers."""
        if self.csv_path.exists():
            return
        
        try:
            with open(self.csv_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(
                    f,
                    fieldnames=["date", "time", "name", "camera_id", "timestamp_iso", "confidence"],
                )
                writer.writeheader()
            logger.info("created attendance csv with headers")
        except Exception as exc:
            logger.error("failed to create csv headers: %s", exc)

    # ------------------------------------------------------------------
    # public API
    # ------------------------------------------------------------------

    def mark(self, student_name: str, confidence: float = 1.0, camera_id: str | None = None) -> bool:
        """Mark student as present with confidence score.
        
        Args:
            student_name: Name of student (will be normalized)
            confidence: Recognition confidence (0.0-1.0)
            camera_id: identifier of camera where recognition occurred
            
        Returns:
            True if new record written, False if already marked today or error
        """
        norm = utils.normalize_student_name(student_name)
        if not norm:
            logger.warning("empty name passed to mark()")
            return False

        # Check session-level duplicates (same person marked twice today)
        if norm.lower() in self._marked:
            self._session_stats["duplicates_prevented"] += 1
            logger.debug("duplicate attendance prevented for %s", norm)
            return False

        # Prepare record
        now = datetime.now()
        date_str = now.strftime("%Y-%m-%d")
        time_str = now.strftime("%H:%M:%S")
        iso_str = now.isoformat()

        try:
            self._ensure_csv_headers()
            
            with open(self.csv_path, "a", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(
                    f,
                    fieldnames=["date", "time", "name", "camera_id", "timestamp_iso", "confidence"],
                )
                writer.writerow({
                    "date": date_str,
                    "time": time_str,
                    "name": norm,
                    "camera_id": camera_id or "",
                    "timestamp_iso": iso_str,
                    "confidence": f"{confidence:.2%}",
                })
        except Exception as exc:
            logger.error("failed to write attendance: %s", exc)
            return False

        # Update session state
        self._marked.add(norm.lower())
        self._session_stats["recognized"] += 1
        
        entry = {
            "name": norm,
            "timestamp": time_str,
            "confidence": f"{confidence:.2%}",
            "status": "[OK] MARKED",  # Use ASCII instead of unicode
        }
        self._recent_entries.appendleft(entry)
        
        logger.info(
            "attendance marked: name=%s, time=%s, confidence=%s",
            norm,
            time_str,
            f"{confidence:.2%}",
        )
        return True

    def log_unknown_face(self, confidence: float = 0.0, camera_id: str | None = None) -> None:
        """Log when an unknown/unrecognized face is detected.
        
        Args:
            confidence: Recognition confidence (if any)
            camera_id: optional camera identifier where unknown face was seen
        """
        now = datetime.now()
        self._session_stats["unknown"] += 1
        
        entry = {
            "name": "UnknownFace",
            "timestamp": now.strftime("%H:%M:%S"),
            "confidence": f"{confidence:.2%}",
            "status": "[??] UNKNOWN",  # Use ASCII instead of unicode
        }
        if camera_id:
            entry["camera_id"] = camera_id
        self._recent_entries.appendleft(entry)
        
        logger.info(
            "unknown face detected at %s (confidence=%.2f) camera=%s",
            now.isoformat(),
            confidence,
            camera_id,
        )

    def get_records(
        self,
        date_str: Optional[str] = None,
        camera_id: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict]:
        """Fetch attendance records.
        
        Args:
            date_str: Filter by date (YYYY-MM-DD), None for all
            camera_id: Filter by camera ID, None for all
            limit: Maximum records to return
            
        Returns:
            List of attendance records as dictionaries
        """
        records: List[Dict] = []
        if not self.csv_path.exists():
            return records
        
        try:
            with open(self.csv_path, newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if date_str and row.get("date") != date_str:
                        continue
                    if camera_id and row.get("camera_id") != camera_id:
                        continue
                    records.append(row)
                    if len(records) >= limit:
                        break
        except Exception as exc:
            logger.warning("failed to read attendance records: %s", exc)
        
        return records

    def get_recent_activity(self, limit: int = 10) -> List[Dict]:
        """Get recent marked/unknown face events."""
        return list(self._recent_entries)[:limit]

    def get_session_stats(self) -> Dict:
        """Return current session statistics."""
        return {
            "recognized_count": self._session_stats["recognized"],
            "unknown_count": self._session_stats["unknown"],
            "duplicates_prevented": self._session_stats["duplicates_prevented"],
            "marked_today": len(self._marked),
        }

    def reset_session(self) -> None:
        """Reset in-session tracking (e.g., for new day)."""
        self._marked.clear()
        self._recent_entries.clear()
        self._today = date.today().isoformat()
        self._session_stats = {
            "recognized": 0,
            "unknown": 0,
            "duplicates_prevented": 0,
        }
        logger.info("attendance session reset")

    # ------------------------------------------------------------------
    # convenience helpers
    # ------------------------------------------------------------------

    def is_marked(self, student_name: str) -> bool:
        """Return ``True`` if the student has already been marked today."""
        norm = utils.normalize_student_name(student_name)
        return norm.lower() in self._marked
