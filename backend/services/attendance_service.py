from __future__ import annotations

import csv
from datetime import date
from pathlib import Path
from typing import List, Dict, Optional

ATTENDANCE_CSV = Path("attendance/attendance.csv")


def _read_csv() -> List[Dict[str, str]]:
    records: List[Dict[str, str]] = []
    if not ATTENDANCE_CSV.exists():
        return records
    try:
        with open(ATTENDANCE_CSV, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                records.append(row)
    except Exception:
        pass
    return records


def get_today_stats() -> Dict[str, int]:
    today = date.today().isoformat()
    records = [r for r in _read_csv() if r.get("date") == today]
    total = len(records)
    # naive "late" detection: any timestamp after 09:00:00
    late = sum(1 for r in records if r.get("time", "") > "09:00:00")
    return {"present_today": total, "late_students": late}


def get_attendance_records(date_str: Optional[str] = None) -> List[Dict[str, str]]:
    recs = _read_csv()
    if date_str:
        return [r for r in recs if r.get("date") == date_str]
    return recs


def get_summary() -> Dict[str, int]:
    records = _read_csv()
    total_students = len({r.get("name") for r in records if r.get("name")})
    return {"total_students": total_students}
