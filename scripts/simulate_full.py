#!/usr/bin/env python3
"""Simulate face recognition and attendance marking."""

import requests
import time
import logging
import random
import csv
import os
from datetime import datetime
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("simulate_faces")

API_URL = "https://ai-attendance-system-vi47.onrender.com/api/mark_attendance"

BASE_DIR = Path(__file__).resolve().parent
CSV_DIR = BASE_DIR.parent / "attendance"
CSV_FILE = CSV_DIR / "attendance.csv"

def ensure_csv():
    if not os.path.exists("attendance"):
        os.makedirs("attendance")
    if not os.path.exists(CSV_FILE):
        with open(CSV_FILE, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["id", "student_name", "date", "time", "camera", "confidence"])

def simulate_detection():
    known_names = ["Kiran", "Student Name"]
    cameras = ["Camera 1", "Camera 2", "Camera 3"]

    for i in range(5):
        name = random.choice(known_names)
        confidence = round(random.uniform(0.85, 0.98), 2)
        camera = random.choice(cameras)

        payload = {
            "student_name": name,
            "confidence": confidence,
            "camera": camera,
        }

        logger.info(f"Simulating detection: {name} (conf={confidence}) from {camera}")

        # Simulate API call
        try:
            resp = requests.post(API_URL, json=payload, timeout=10)
            logger.info(f"API Response: {resp.status_code}")
            if resp.status_code == 200:
                logger.info("Attendance marked successfully")
            else:
                logger.warning(f"API failed: {resp.text}")
        except Exception as e:
            logger.error(f"API error: {e}")

        # Also write to local CSV for verification
        now = datetime.now()
        date = now.strftime("%Y-%m-%d")
        time_str = now.strftime("%H:%M:%S")

        with open(CSV_FILE, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([i+1, name, date, time_str, camera, confidence])

        time.sleep(2)

def verify_apis():
    logger.info("Verifying APIs...")

    # Simulate GET /api/attendance
    try:
        resp = requests.get("https://ai-attendance-system-vi47.onrender.com/api/attendance", timeout=10)
        logger.info(f"Attendance API: {resp.status_code}")
        if resp.status_code == 200:
            data = resp.json()
            logger.info(f"Records: {len(data) if isinstance(data, list) else 'N/A'}")
        else:
            logger.warning(f"Attendance API failed: {resp.text}")
    except Exception as e:
        logger.error(f"Attendance API error: {e}")

    # Simulate GET /api/stats
    try:
        resp = requests.get("https://ai-attendance-system-vi47.onrender.com/api/stats", timeout=10)
        logger.info(f"Stats API: {resp.status_code}")
        if resp.status_code == 200:
            data = resp.json()
            logger.info(f"Stats: {data}")
        else:
            logger.warning(f"Stats API failed: {resp.text}")
    except Exception as e:
        logger.error(f"Stats API error: {e}")

    # Show local CSV
    if os.path.exists(CSV_FILE):
        with open(CSV_FILE, 'r') as f:
            lines = f.readlines()
            logger.info(f"Local CSV has {len(lines)-1} records")
            for line in lines[-6:]:  # last 5 + header
                logger.info(line.strip())

def main():
    ensure_csv()
    simulate_detection()
    verify_apis()

if __name__ == '__main__':
    main()
