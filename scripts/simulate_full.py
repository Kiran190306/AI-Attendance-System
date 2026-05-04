#!/usr/bin/env python3
"""Continuously simulate face recognition and attendance marking."""

import requests
import time
import logging
import random
import csv
import os
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

# Student pool for simulation
STUDENT_POOL = [
    "Kiran", "Priya", "Arjun", "Meera", "Rohan",
    "Isha", "Vikram", "Anjali", "Dev", "Neha"
]

CAMERA_POOL = ["cam1", "cam2", "cam3"]

# Track last marked time to prevent duplicates
last_marked_time = {}
DUPLICATE_PREVENTION_INTERVAL = 30  # seconds


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
            logger.info(
                "POST attempt %d: %s status=%d",
                attempt,
                url,
                resp.status_code
            )
            if resp.status_code in (200, 201):
                logger.info("✓ Attendance marked: %s", payload)
                return resp
            logger.warning(
                "POST attempt %d failed: status=%d body=%s",
                attempt,
                resp.status_code,
                resp.text[:200]
            )
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
        if resp.status_code == 200:
            data = resp.json()
            count = len(data) if isinstance(data, list) else 0
            logger.info("Current attendance records: %d", count)
            return count
        logger.warning("GET /api/attendance failed: %d", resp.status_code)
    except Exception as e:
        logger.error("GET /api/attendance error: %s", str(e))
    return 0


def simulate_detection():
    """Generate random attendance entry."""
    name = random.choice(STUDENT_POOL)
    now_time = time.time()
    
    # Check duplicate prevention
    last_mark = last_marked_time.get(name, 0)
    if (now_time - last_mark) < DUPLICATE_PREVENTION_INTERVAL:
        logger.debug(
            "Skip %s: marked %.1f seconds ago (threshold=%d)",
            name,
            now_time - last_mark,
            DUPLICATE_PREVENTION_INTERVAL
        )
        return False
    
    confidence = round(random.uniform(0.85, 0.99), 2)
    camera = random.choice(CAMERA_POOL)
    
    payload = {
        "name": name,
        "confidence": confidence,
        "camera": camera,
    }
    
    logger.info(
        "Detecting face: %s (conf=%.2f, camera=%s)",
        name,
        confidence,
        camera
    )
    
    resp = post_with_retry(API_URL, payload)
    if resp is not None and resp.status_code in (200, 201):
        last_marked_time[name] = now_time
        
        # Write to local CSV for local verification
        now = datetime.now()
        date_val = now.strftime("%Y-%m-%d")
        time_str = now.strftime("%H:%M:%S")
        
        try:
            with open(CSV_FILE, 'a', newline='') as f:
                writer = csv.writer(f)
                row_id = sum(1 for line in open(CSV_FILE)) if CSV_FILE.exists() else 1
                writer.writerow([row_id, name, date_val, time_str, camera, confidence])
        except Exception as e:
            logger.error("Error writing to CSV: %s", str(e))
        
        return True
    return False


def main():
    """Main simulation loop."""
    logger.info("=" * 60)
    logger.info("AI ATTENDANCE SIMULATOR - STARTING")
    logger.info("API URL: %s", API_URL)
    logger.info("Student Pool: %s", STUDENT_POOL)
    logger.info("Duplicate Prevention: %d seconds", DUPLICATE_PREVENTION_INTERVAL)
    logger.info("=" * 60)
    
    ensure_csv()
    
    iteration = 0
    try:
        while True:
            iteration += 1
            logger.info("\n[Iteration %d] Starting detection cycle...", iteration)
            
            # Simulate 1-3 detections per cycle
            detections_this_cycle = random.randint(1, 3)
            for _ in range(detections_this_cycle):
                simulate_detection()
                time.sleep(random.uniform(1, 3))
            
            # Check current count
            current_count = get_attendance_count()
            logger.info(
                "[Iteration %d] Cycle complete. Total records: %d",
                iteration,
                current_count
            )
            
            # Wait before next cycle
            wait_time = random.uniform(5, 10)
            logger.info("Waiting %.1f seconds before next cycle...\n", wait_time)
            time.sleep(wait_time)
    except KeyboardInterrupt:
        logger.info("\n" + "=" * 60)
        logger.info("SIMULATOR STOPPED BY USER")
        logger.info("=" * 60)
    except Exception as e:
        logger.error("Simulator error: %s", str(e), exc_info=True)
        raise


if __name__ == '__main__':
    main()
