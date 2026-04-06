"""Handles writing presence analytics to CSV file."""
from __future__ import annotations

import csv
from pathlib import Path
from typing import Dict


class SessionLogger:
    def __init__(self, path: str = "analytics/session_log.csv"):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            with self.path.open("w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow([
                    "name",
                    "time_present",
                    "focus_percent",
                    "distraction_percent",
                    "blink_count",
                ])

    def log(self, record: Dict) -> None:
        # record should contain keys matching header
        with self.path.open("a", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([
                record.get("name", ""),
                record.get("time_present", 0),
                record.get("focus_percent", 0),
                record.get("distraction_percent", 0),
                record.get("blink_count", 0),
            ])
