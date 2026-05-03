from __future__ import annotations

import sqlite3
import logging
import requests
from datetime import datetime, date
from pathlib import Path
from typing import List, Optional, Tuple, Set, Dict
from collections import deque

from . import config, utils

logger = logging.getLogger(__name__)


class AttendanceServiceError(Exception):
    """Raised when attendance operations fail."""
    pass


def sync_to_cloud(name: str, date_str: str, time_str: str, confidence: float = 1.0, camera_id: str | None = None) -> bool:
    """Send attendance record to cloud backend.
    
    This function attempts to sync marked attendance to the cloud API.
    If the cloud is unavailable, attendance is still recorded locally.
    
    Args:
        name: Student name
        date_str: Date in YYYY-MM-DD format
        time_str: Time in HH:MM:SS format
        confidence: Recognition confidence (0.0-1.0)
        camera_id: Camera identifier
        
    Returns:
        True if sync successful or skipped gracefully, False on critical error
    """
    try:
        from . import cloud_config
        
        # Skip if cloud sync is disabled
        if not cloud_config.CLOUD_SYNC_ENABLED:
            return True
        
        cloud_url = cloud_config.CLOUD_API_URL
    except ImportError:
        # Fallback to hardcoded URL if config not available
        cloud_url = "http://localhost:10000/api/attendance/mark"
    
    payload = {
        "name": name,
        "date": date_str,
        "time": time_str,
        "confidence": confidence,
        "camera_id": camera_id or "local"
    }
    
    try:
        response = requests.post(cloud_url, json=payload, timeout=3)
        if response.status_code in [200, 201]:
            logger.info(f"Cloud sync successful for {name}")
            return True
        else:
            logger.warning(f"Cloud sync failed with status {response.status_code}")
            return False
    except requests.exceptions.Timeout:
        logger.warning("Cloud sync timeout - local record saved")
        return True  # Local record was saved, so don't fail
    except requests.exceptions.ConnectionError:
        logger.debug("Cloud service not available - local record saved")
        return True  # Local record was saved, so don't fail
    except Exception as e:
        logger.warning(f"Cloud sync error: {str(e)} - local record saved")
        return True  # Local record was saved, so don't fail


class AttendanceService:
    """SQLite-based attendance logger with comprehensive features.
    
    Features:
    - Stores attendance in SQLite database (attendance.db)
    - Prevents duplicate attendance per student per day
    - Tracks timestamp and status
    - Logs unknown face detections
    - Session statistics tracking
    - Production-grade error handling
    
    Table: attendance (id, name, time, status)
    """

    def __init__(self, db_path: Path | str = config.ATTENDANCE_DB) -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        self._today = date.today().isoformat()
        self._marked: Set[str] = set()  # session-level duplicates today
        self._recent_entries: deque = deque(maxlen=10)  # recent activity
        
        # Session statistics
        self._session_stats = {
            "recognized": 0,
            "unknown": 0,
            "duplicates_prevented": 0,
        }
        
        self._init_db()
        self._load_existing()
        logger.info("attendance service initialized (db: %s)", self.db_path)

    # ------------------------------------------------------------------
    # internal helpers
    # ------------------------------------------------------------------

    def _init_db(self) -> None:
        """Initialize SQLite database and create table if not exists."""
        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS attendance (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL,
                        time TEXT NOT NULL,
                        status TEXT NOT NULL,
                        date TEXT NOT NULL,
                        confidence REAL,
                        camera_id TEXT,
                        timestamp_iso TEXT
                    )
                ''')
                # Create index for faster queries
                conn.execute('CREATE INDEX IF NOT EXISTS idx_date ON attendance(date)')
                conn.execute('CREATE INDEX IF NOT EXISTS idx_name ON attendance(name)')
                conn.commit()
        except Exception as exc:
            logger.error("failed to initialize database: %s", exc)
            raise AttendanceServiceError(f"Database initialization failed: {exc}")

    def _load_existing(self) -> None:
        """Load today's records to prevent duplicates."""
        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                cursor = conn.execute(
                    "SELECT name FROM attendance WHERE date = ? AND status = 'present'",
                    (self._today,)
                )
                for row in cursor:
                    name = row[0].lower().strip()
                    if name:
                        self._marked.add(name)
        except Exception as exc:
            logger.warning("failed to load existing attendance: %s", exc)

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
            with sqlite3.connect(str(self.db_path)) as conn:
                conn.execute('''
                    INSERT INTO attendance (name, time, status, date, confidence, camera_id, timestamp_iso)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (norm, time_str, 'present', date_str, confidence, camera_id or "", iso_str))
                conn.commit()
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
        
        # Attempt to sync to cloud backend (non-blocking, doesn't affect local recording)
        try:
            sync_to_cloud(norm, date_str, time_str, confidence, camera_id)
        except Exception as e:
            logger.debug(f"Cloud sync attempted: {str(e)}")
        
        return True

    def log_unknown_face(self, confidence: float = 0.0, camera_id: str | None = None) -> None:
        """Log when an unknown/unrecognized face is detected.
        
        Args:
            confidence: Recognition confidence (if any)
            camera_id: optional camera identifier where unknown face was seen
        """
        now = datetime.now()
        date_str = now.strftime("%Y-%m-%d")
        time_str = now.strftime("%H:%M:%S")
        iso_str = now.isoformat()
        
        self._session_stats["unknown"] += 1
        
        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                conn.execute('''
                    INSERT INTO attendance (name, time, status, date, confidence, camera_id, timestamp_iso)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', ("UnknownFace", time_str, 'unknown', date_str, confidence, camera_id or "", iso_str))
                conn.commit()
        except Exception as exc:
            logger.warning("failed to log unknown face: %s", exc)
        
        entry = {
            "name": "UnknownFace",
            "timestamp": time_str,
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
        
        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                query = "SELECT id, name, time, status, date, confidence, camera_id, timestamp_iso FROM attendance"
                params = []
                
                conditions = []
                if date_str:
                    conditions.append("date = ?")
                    params.append(date_str)
                if camera_id:
                    conditions.append("camera_id = ?")
                    params.append(camera_id)
                
                if conditions:
                    query += " WHERE " + " AND ".join(conditions)
                
                query += " ORDER BY timestamp_iso DESC LIMIT ?"
                params.append(limit)
                
                cursor = conn.execute(query, params)
                columns = [desc[0] for desc in cursor.description]
                
                for row in cursor:
                    record = dict(zip(columns, row))
                    # Convert confidence to percentage string for compatibility
                    if 'confidence' in record and record['confidence'] is not None:
                        record['confidence'] = f"{record['confidence']:.2%}"
                    records.append(record)
                    
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
