#!/usr/bin/env python3
"""Simple face recognition script that posts attendance to backend.

Usage:
    python scripts/mark_attendance_from_camera.py --api https://ai-attendance-system-vi47.onrender.com/api/mark_attendance
"""
import face_recognition
import cv2
import numpy as np
import os
import requests
import time
import argparse
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("face_mark")

DEFAULT_API_URL = "https://ai-attendance-system-vi47.onrender.com/api/mark_attendance"


def load_known_faces(dataset_dir):
    known_encodings = []
    known_names = []
    if not os.path.isdir(dataset_dir):
        logger.warning("Dataset directory not found: %s", dataset_dir)
        return known_encodings, known_names
    for person in os.listdir(dataset_dir):
        person_dir = os.path.join(dataset_dir, person)
        if not os.path.isdir(person_dir):
            continue
        for fn in os.listdir(person_dir):
            path = os.path.join(person_dir, fn)
            try:
                img = face_recognition.load_image_file(path)
                encs = face_recognition.face_encodings(img)
                if encs:
                    known_encodings.append(encs[0])
                    known_names.append(person)
                    logger.info("Loaded encoding for %s from %s", person, path)
            except Exception as e:
                logger.warning("Failed to process %s: %s", path, e)
    return known_encodings, known_names


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--api", default=DEFAULT_API_URL)
    parser.add_argument("--dataset", default="dataset")
    parser.add_argument("--camera", type=int, default=0)
    parser.add_argument("--tolerance", type=float, default=0.5)
    parser.add_argument("--interval", type=int, default=60, help="minimum seconds between marking same student")
    parser.add_argument("--retries", type=int, default=3, help="number of retries for failed POST requests")
    args = parser.parse_args()

    known_encodings, known_names = load_known_faces(args.dataset)
    if not known_encodings:
        logger.error("No known faces loaded; exiting")
        return

    last_marked = {}

    video_capture = cv2.VideoCapture(args.camera)
    if not video_capture.isOpened():
        logger.error("Cannot open camera %s", args.camera)
        return

    try:
        while True:
            ret, frame = video_capture.read()
            if not ret:
                break

            # Resize frame for faster processing
            small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
            rgb_small = small_frame[:, :, ::-1]

            face_locations = face_recognition.face_locations(rgb_small)
            face_encodings = face_recognition.face_encodings(rgb_small, face_locations)

            for face_encoding, face_location in zip(face_encodings, face_locations):
                distances = face_recognition.face_distance(known_encodings, face_encoding)
                if len(distances) == 0:
                    continue
                best_idx = np.argmin(distances)
                best_dist = float(distances[best_idx])
                match = best_dist <= args.tolerance
                name = known_names[best_idx] if match else "Unknown"
                confidence = max(0.0, 1.0 - best_dist) if match else 0.0

                if match:
                    now = time.time()
                    last = last_marked.get(name)
                    if last is None or (now - last) >= args.interval:
                        payload = {
                            "name": name,
                            "confidence": round(confidence, 2),
                            "camera": f"cam{args.camera}",
                        }
                        success = False
                        for attempt in range(1, args.retries + 1):
                            try:
                                resp = requests.post(args.api, json=payload, timeout=10)
                                if resp.status_code in (200, 201):
                                    logger.info("Marked attendance for %s (conf=%.2f) on attempt %s", name, confidence, attempt)
                                    last_marked[name] = now
                                    success = True
                                    break
                                logger.warning("Attempt %s failed for %s: %s %s", attempt, name, resp.status_code, resp.text)
                            except Exception as e:
                                logger.warning("Attempt %s error posting attendance for %s: %s", attempt, name, e)
                            time.sleep(min(2 ** attempt, 10))
                        if not success:
                            logger.error("Unable to post attendance for %s after %s attempts", name, args.retries)

                # Draw box around face
                top, right, bottom, left = face_location
                # scale back up
                top *= 4
                right *= 4
                bottom *= 4
                left *= 4
                cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
                cv2.putText(frame, f"{name}", (left, top - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)

            cv2.imshow('Video', frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
    finally:
        video_capture.release()
        cv2.destroyAllWindows()


if __name__ == '__main__':
    main()
