import csv
import logging
from datetime import datetime, date
from pathlib import Path
from typing import Set, Dict

from .. import config
from ..utils import helpers
from ..database.db import SessionLocal
from ..database.repository import AttendanceRepository

logger = logging.getLogger(__name__)


class AttendanceServiceError(Exception):
    pass


class AttendanceService:
    def __init__(self, csv_path: Path | str = config.ATTENDANCE_CSV) -> None:
        self.csv_path = Path(csv_path)
        self.csv_path.parent.mkdir(parents=True, exist_ok=True)
        self._today = date.today().isoformat()
        self._marked: Set[str] = set()
        self._recent: list[Dict] = []
        self._stats = {"recognized": 0, "unknown": 0, "duplicates_prevented": 0}
        self._load_existing()
        logger.info("attendance service initialized (csv: %s)", self.csv_path)

    def _load_existing(self) -> None:
        if not self.csv_path.exists():
            return
        try:
            with open(self.csv_path, newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row.get("date") == self._today:
                        name = row.get("name", "").lower().strip()
                        if name:
                            self._marked.add(name)
        except Exception as exc:
            logger.warning("failed to load existing attendance: %s", exc)

    def _ensure_csv_headers(self) -> None:
        if self.csv_path.exists():
            return
        try:
            with open(self.csv_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(
                    f,
                    fieldnames=["date", "time", "name", "timestamp_iso", "confidence", "camera_id", "camera_name"],
                )
                writer.writeheader()
            logger.info("created attendance csv with headers")
        except Exception as exc:
            logger.error("failed to create csv headers: %s", exc)

    def mark(
        self,
        student_name: str,
        confidence: float = 1.0,
        camera_id: int | None = None,
        camera_name: str | None = None,
    ) -> bool:
        norm = helpers.normalize_student_name(student_name)
        if not norm:
            logger.warning("empty name passed to mark()")
            return False
        if norm.lower() in self._marked:
            self._stats["duplicates_prevented"] += 1
            logger.debug("duplicate attendance prevented for %s", norm)
            return False
        now = datetime.now()
        date_str = now.strftime("%Y-%m-%d")
        time_str = now.strftime("%H:%M:%S")
        iso_str = now.isoformat()
        try:
            self._ensure_csv_headers()
            with open(self.csv_path, "a", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(
                    f,
                    fieldnames=["date", "time", "name", "timestamp_iso", "confidence", "camera_id", "camera_name"],
                )
                row = {
                    "date": date_str,
                    "time": time_str,
                    "name": norm,
                    "timestamp_iso": iso_str,
                    "confidence": f"{confidence:.2%}",
                }
                if camera_id is not None:
                    row["camera_id"] = camera_id
                if camera_name is not None:
                    row["camera_name"] = camera_name
                writer.writerow(row)
        except Exception as exc:
            logger.error("failed to write attendance: %s", exc)
            return False
        # update in-memory
        self._marked.add(norm.lower())
        self._stats["recognized"] += 1
        self._recent.insert(0, {"name": norm, "timestamp": time_str, "confidence": f"{confidence:.2%}"})
        # write to db (include camera info when available)
        db = SessionLocal()
        try:
            AttendanceRepository.add_entry(db, norm, confidence, timestamp=now, camera=camera_name)
        except Exception as exc:
            logger.error("db write failed: %s", exc)
        finally:
            db.close()
        logger.info(
            "attendance marked: name=%s time=%s confidence=%s",
            norm,
            time_str,
            f"{confidence:.2%}",
        )
        return True

    def log_unknown(self, confidence: float = 0.0) -> None:
        now = datetime.now()
        self._stats["unknown"] += 1
        self._recent.insert(0, {"name": "Unknown", "timestamp": now.strftime("%H:%M:%S"), "confidence": f"{confidence:.2%}"})
        logger.info("unknown face detected at %s (confidence=%.2f)", now.isoformat(), confidence)

    def get_records(self, date_str: str | None = None, limit: int = 100):
        records = []
        try:
            with open(self.csv_path, newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if date_str and row.get("date") != date_str:
                        continue
                    records.append(row)
                    if len(records) >= limit:
                        break
        except Exception:
            pass
        return records

    def get_today_records(self):
        return self.get_records(date_str=self._today)

    def get_session_stats(self):
        return {
            "recognized_count": self._stats["recognized"],
            "unknown_count": self._stats["unknown"],
            "duplicates_prevented": self._stats["duplicates_prevented"],
            "marked_today": len(self._marked),
        }

    def get_recent_activity(self, limit: int = 10):
        return self._recent[:limit]

    def reset_session(self):
        self._marked.clear()
        self._recent.clear()
        self._today = date.today().isoformat()
        self._stats = {"recognized": 0, "unknown": 0, "duplicates_prevented": 0}
        logger.info("attendance session reset")
