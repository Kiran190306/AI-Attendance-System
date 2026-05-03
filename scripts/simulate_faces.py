#!/usr/bin/env python3
"""Simulate face recognition without camera by posting test entries."""

import requests
import time
import logging
import random

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("simulate_faces")

API_URL = "https://ai-attendance-system-vi47.onrender.com/api/mark_attendance"

def simulate_faces():
    # Known faces from dataset
    known_names = ["Kiran", "Student Name"]
    
    # Simulate 5 detections
    for i in range(5):
        # Randomly select a name
        name = random.choice(known_names)
        confidence = round(random.uniform(0.85, 0.98), 2)
        camera = f"Camera {random.randint(1,3)}"
        
        payload = {
            "student_name": name,
            "confidence": confidence,
            "camera": camera,
        }
        
        try:
            logger.info(f"Simulating detection: {name} (conf={confidence})")
            resp = requests.post(API_URL, json=payload, timeout=10)
            logger.info(f"API Response: {resp.status_code}")
            if resp.status_code == 200:
                logger.info("Attendance marked successfully")
            else:
                logger.warning(f"Failed: {resp.text}")
        except Exception as e:
            logger.error(f"Error posting: {e}")
        
        time.sleep(2)  # simulate time between detections

if __name__ == '__main__':
    simulate_faces()
