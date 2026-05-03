#!/usr/bin/env python3
"""Simulate face recognition by posting test attendance entries to API."""

import requests
import time
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("simulate_faces")

API_URL = "https://ai-attendance-system-vi47.onrender.com/api/mark_attendance"

def simulate_attendance():
    # Simulate 3 attendance entries
    test_entries = [
        {"student_name": "Alice Smith", "confidence": 0.95, "camera": "Camera 1"},
        {"student_name": "Bob Johnson", "confidence": 0.92, "camera": "Camera 1"},
        {"student_name": "Carol Lee", "confidence": 0.88, "camera": "Camera 2"},
    ]

    for entry in test_entries:
        try:
            logger.info(f"Posting attendance for {entry['student_name']}")
            resp = requests.post(API_URL, json=entry, timeout=10)
            logger.info(f"Response: {resp.status_code} - {resp.text}")
            time.sleep(1)  # simulate interval
        except Exception as e:
            logger.error(f"Failed to post {entry['student_name']}: {e}")

if __name__ == '__main__':
    simulate_attendance()
