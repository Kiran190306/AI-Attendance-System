#!/usr/bin/env python3
"""Continuously simulate attendance marking without camera input."""

import requests
import time
import logging
import random
import csv
import threading
from datetime import datetime
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("attendance_simulator")

API_URL = "https://ai-attendance-system-vi47.onrender.com/api/mark_attendance"
GET_URL = "https://ai-attendance-system-vi47.onrender.com/api/attendance"

BASE_DIR = Path(__file__).resolve().parent
CSV_DIR = BASE_DIR.parent / "attendance"
CSV_FILE = CSV_DIR / "attendance.csv"

STUDENT_POOL = [
    "Kiran", "Priya", "Arjun", "Meera", "Rohan",
    "Isha", "Vikram", "Anjali", "Dev", "Neha"
]

CAMERA_POOL = ["cam1", "cam2", "cam3"]

last_marked_time = {}
DUPLICATE_PREVENTION_INTERVAL = 45  # seconds
stop_event = threading.Event()


def ensure_csv():
    CSV_DIR.mkdir(parents=True, exist_ok=True)
    if not CSV_FILE.exists():
        with open(CSV_FILE, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["id", "name", "date", "time", "camera", "confidence"])
        logger.info(f"Created CSV file at {CSV_FILE}")


def post_with_retry(url, payload, retries=3, timeout=10):
    """Post attendance with exponential backoff retry."""
    for attempt in range(1, retries + 1):
        try:
            resp = requests.post(url, json=payload, timeout=timeout)
            logger.info("POST attempt %d to %s status=%d", attempt, url, resp.status_code)
            logger.info("POST payload: %s", payload)
            logger.info("POST response body: %s", resp.text.strip())
            if resp.status_code in (200, 201):
                return resp
            logger.warning("POST attempt %d failed: status=%d", attempt, resp.status_code)
        except Exception as e:
            logger.warning("POST attempt %d error: %s", attempt, str(e))

        if attempt < retries:
            backoff = min(2 ** attempt, 10)
            logger.info("Retrying in %d seconds...", backoff)
            time.sleep(backoff)

    logger.error("Failed to post attendance after %d attempts", retries)
    return None


def get_attendance_count():
    """Fetch current attendance count from API."""
    try:
        resp = requests.get(GET_URL, timeout=10)
        logger.info("GET /api/attendance status=%d", resp.status_code)
        if resp.status_code == 200:
            data = resp.json()
            count = len(data) if isinstance(data, list) else 0
            logger.info("Current attendance records: %d", count)
            return count
        logger.warning("GET /api/attendance failed: %d", resp.status_code)
    except Exception as e:
        logger.error("GET /api/attendance error: %s", str(e))
    return 0


def simulate_detection(students):
    """Generate a random attendance event."""
    name = random.choice(students)
    now_time = time.time()

    last_mark = last_marked_time.get(name, 0)
    if (now_time - last_mark) < DUPLICATE_PREVENTION_INTERVAL:
        logger.info("Duplicate prevention: skipping %s, last marked %.1f seconds ago", name, now_time - last_mark)
        return False

    confidence = round(random.uniform(0.85, 0.99), 2)
    camera = random.choice(CAMERA_POOL)
    payload = {
        "name": name,
        "confidence": confidence,
        "camera": camera,
    }

    logger.info("Posting attendance for %s (confidence=%.2f, camera=%s)", name, confidence, camera)
    resp = post_with_retry(API_URL, payload)

    if resp is not None and resp.status_code in (200, 201):
        last_marked_time[name] = now_time
        logger.info("Attendance successfully posted for %s", name)

        now = datetime.now()
        date_val = now.strftime("%Y-%m-%d")
        time_str = now.strftime("%H:%M:%S")
        try:
            with open(CSV_FILE, 'a', newline='') as f:
                writer = csv.writer(f)
                row_id = sum(1 for _ in open(CSV_FILE)) if CSV_FILE.exists() else 1
                writer.writerow([row_id, name, date_val, time_str, camera, confidence])
        except Exception as e:
            logger.error("Error writing to CSV: %s", str(e))
        return True

    logger.warning("Attendance post failed for %s", name)
    return False


def attendance_scheduler(students):
    """Send attendance events in a scheduled loop."""
    while not stop_event.is_set():
        simulate_detection(students)
        interval = random.uniform(5, 10)
        logger.info("Next attendance event in %.1f seconds", interval)
        stop_event.wait(interval)


def monitor_attendance():
    """Poll the attendance count periodically."""
    while not stop_event.is_set():
        get_attendance_count()
        stop_event.wait(15)


def main():
    logger.info("=" * 60)
    logger.info("AI ATTENDANCE SIMULATOR - STARTING")
    logger.info("API URL: %s", API_URL)
    logger.info("Duplicate Prevention: %d seconds", DUPLICATE_PREVENTION_INTERVAL)
    logger.info("=" * 60)

    ensure_csv()

    active_students = random.sample(STUDENT_POOL, random.randint(5, min(10, len(STUDENT_POOL))))
    logger.info("Simulating attendance for students: %s", ", ".join(active_students))

    scheduler_thread = threading.Thread(target=attendance_scheduler, args=(active_students,), daemon=True)
    monitor_thread = threading.Thread(target=monitor_attendance, daemon=True)

    scheduler_thread.start()
    monitor_thread.start()

    try:
        while scheduler_thread.is_alive() and monitor_thread.is_alive():
            scheduler_thread.join(timeout=1)
            monitor_thread.join(timeout=1)
    except KeyboardInterrupt:
        logger.info("Stopping simulator...")
        stop_event.set()
        scheduler_thread.join()
        monitor_thread.join()
        logger.info("Simulator stopped.")


if __name__ == '__main__':
    main()
