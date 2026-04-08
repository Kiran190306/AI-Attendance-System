"""
Extended Attendance Service with Cloud Sync Integration
"""

import csv
import logging
from datetime import datetime, date
from pathlib import Path
from typing import List, Optional, Tuple, Set, Dict
from collections import deque

from core import config, utils

# Import sync client
try:
    from sync import get_sync_client
except ImportError:
    def get_sync_client(): return None

logger = logging.getLogger(__name__)


class AttendanceServiceError(Exception):
    """Raised when attendance operations fail."""
    pass


class AttendanceServiceWithCloudSync:
    """
    Enhanced Attendance Service with Cloud Sync capability.
    
    Features:
    - All features from original AttendanceService
    - Automatic cloud sync of marked attendance
    - Queue management for offline operation
    - Configurable sync behavior
    """

    def __init__(
        self,
        csv_path: Path | str = config.ATTENDANCE_CSV,
        enable_cloud_sync: bool = True,
    ) -> None:
        """
        Initialize Attendance Service with Cloud Sync.
        
        Args:
            csv_path: Path to attendance CSV file
            enable_cloud_sync: Enable automatic cloud synchronization
        """
        self.csv_path = Path(csv_path)
        self.csv_path.parent.mkdir(parents=True, exist_ok=True)
        
        self.enable_cloud_sync = enable_cloud_sync
        self.sync_client = get_sync_client() if enable_cloud_sync else None
        
        self._today = date.today().isoformat()
        self._marked: Set[str] = set()
        self._recent_entries: deque = deque(maxlen=10)
        
        # Session statistics
        self._session_stats = {
            "recognized": 0,
            "unknown": 0,
            "duplicates_prevented": 0,
            "cloud_synced": 0,
            "cloud_failed": 0,
        }
        
        self._load_existing()
        logger.info(
            "attendance service initialized (csv: %s, cloud_sync: %s)",
            self.csv_path,
            enable_cloud_sync
        )

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

    def _sync_to_cloud(self, record: Dict) -> bool:
        """
        Attempt to sync record to cloud.
        
        Args:
            record: Attendance record
        
        Returns:
            True if synced or queued, False if sync disabled
        """
        if not self.enable_cloud_sync or not self.sync_client:
            return False
        
        try:
            # Queue record for sync
            self.sync_client.queue_attendance(record)
            self._session_stats["cloud_synced"] += 1
            logger.info(f"Record queued for cloud sync: {record['name']}")
            return True
        except Exception as e:
            logger.error(f"Failed to queue record for sync: {e}")
            self._session_stats["cloud_failed"] += 1
            return False

    # ------------------------------------------------------------------
    # public API
    # ------------------------------------------------------------------

    def mark(self, student_name: str, confidence: float = 1.0, camera_id: str | None = None) -> bool:
        """
        Mark student as present with confidence score.
        
        Automatically syncs to cloud if enabled.
        
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
            
            # Write to local CSV
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

        # Sync to cloud
        cloud_record = {
            "name": norm,
            "confidence": confidence,
            "camera_id": camera_id or "local",
            "timestamp_iso": iso_str,
            "date": date_str,
            "time": time_str,
        }
        self._sync_to_cloud(cloud_record)

        # Update session state
        self._marked.add(norm.lower())
        self._session_stats["recognized"] += 1
        
        entry = {
            "name": norm,
            "timestamp": time_str,
            "confidence": f"{confidence:.2%}",
            "status": "[OK] MARKED",
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
        """Log when an unknown/unrecognized face is detected."""
        now = datetime.now()
        self._session_stats["unknown"] += 1
        
        entry = {
            "name": "UnknownFace",
            "timestamp": now.strftime("%H:%M:%S"),
            "confidence": f"{confidence:.2%}",
            "status": "[??] UNKNOWN",
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
        """Fetch attendance records."""
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
        """Return current session statistics including cloud sync stats."""
        stats = {
            "recognized_count": self._session_stats["recognized"],
            "unknown_count": self._session_stats["unknown"],
            "duplicates_prevented": self._session_stats["duplicates_prevented"],
            "marked_today": len(self._marked),
            "cloud_sync_enabled": self.enable_cloud_sync,
            "cloud_synced": self._session_stats["cloud_synced"],
            "cloud_failed": self._session_stats["cloud_failed"],
        }
        
        # Add sync client stats if available
        if self.sync_client:
            sync_stats = self.sync_client.get_stats()
            stats["sync_health"] = {
                "pending_records": sync_stats.get("pending_records", 0),
                "total_synced": sync_stats.get("total_synced", 0),
                "total_failed": sync_stats.get("total_failed", 0),
                "last_sync_time": sync_stats.get("last_sync_time"),
            }
            stats["is_sync_healthy"] = self.sync_client.is_healthy()
        
        return stats

    def reset_session(self) -> None:
        """Reset in-session tracking (e.g., for new day)."""
        self._marked.clear()
        self._recent_entries.clear()
        self._today = date.today().isoformat()
        self._session_stats = {
            "recognized": 0,
            "unknown": 0,
            "duplicates_prevented": 0,
            "cloud_synced": 0,
            "cloud_failed": 0,
        }
        logger.info("attendance session reset")

    def is_marked(self, student_name: str) -> bool:
        """Return ``True`` if the student has already been marked today."""
        norm = utils.normalize_student_name(student_name)
        return norm.lower() in self._marked

    def force_cloud_sync(self) -> bool:
        """
        Force immediate sync of pending records to cloud.
        
        Returns:
            True if sync client available, False otherwise
        """
        if not self.sync_client:
            logger.warning("Sync client not available")
            return False
        
        try:
            self.sync_client.force_sync()
            logger.info("Forced cloud sync")
            return True
        except Exception as e:
            logger.error(f"Error forcing sync: {e}")
            return False

    def get_sync_status(self) -> Dict:
        """Get cloud sync status."""
        if not self.sync_client:
            return {"enabled": False, "status": "Sync client not initialized"}
        
        return {
            "enabled": self.enable_cloud_sync,
            "is_running": self.sync_client.running,
            "stats": self.sync_client.get_stats(),
            "is_healthy": self.sync_client.is_healthy(),
        }
