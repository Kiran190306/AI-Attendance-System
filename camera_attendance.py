#!/usr/bin/env python3
"""Real-time camera attendance with face recognition.

This script uses the webcam to detect and recognize faces against saved encodings.
Recognized students are marked through the attendance API and duplicate marking is
prevented using a cooldown period.
"""

import argparse
import json
import logging
import pickle
import sys
import time
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

try:
    import cv2
except ImportError as exc:
    raise SystemExit("OpenCV is required. Install with: pip install opencv-python") from exc

try:
    import face_recognition
except ImportError as exc:
    raise SystemExit("face_recognition is required. Install with: pip install face-recognition") from exc

import numpy as np

LOG = logging.getLogger(__name__)


def parse_args():
    parser = argparse.ArgumentParser(
        description="Run webcam-based attendance marking using face encodings."
    )
    parser.add_argument(
        "--api-url",
        default=(__import__('os').environ.get('CLOUD_API_URL') or __import__('os').environ.get('API_URL') or 'http://127.0.0.1:5000'),
        help="Base URL for the attendance API (override with CLOUD_API_URL env var)",
    )
    parser.add_argument(
        "--dataset",
        default="dataset",
        help="Dataset directory containing student folders with face images",
    )
    parser.add_argument(
        "--encodings",
        default="dataset/encodings.pkl",
        help="Path to saved encodings pickle file",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.60,
        help="Embedding distance threshold for recognition",
    )
    parser.add_argument(
        "--cooldown",
        type=float,
        default=10.0,
        help="Seconds to wait before marking the same student again",
    )
    parser.add_argument(
        "--camera",
        type=int,
        default=0,
        help="Webcam device index",
    )
    parser.add_argument(
        "--width",
        type=int,
        default=1280,
        help="Capture width for the webcam",
    )
    parser.add_argument(
        "--height",
        type=int,
        default=720,
        help="Capture height for the webcam",
    )
    parser.add_argument(
        "--no-save-encodings",
        action="store_true",
        help="Do not write generated encodings to disk",
    )
    return parser.parse_args()


def normalize_name(name: str) -> str:
    return " ".join(name.strip().title().split()) if isinstance(name, str) else ""


def load_encodings(encodings_path: Path):
    if not encodings_path.exists():
        LOG.info("Encodings file not found: %s", encodings_path)
        return {}

    try:
        with encodings_path.open("rb") as handle:
            payload = pickle.load(handle)
            known = payload.get("encodings", {}) if isinstance(payload, dict) else {}
            if not isinstance(known, dict):
                LOG.warning("Encodings file is malformed, scanning dataset instead")
                return {}
            LOG.info("Loaded %d known student encodings from %s", len(known), encodings_path)
            return {normalize_name(name): np.asarray(enc, dtype=np.float32) for name, enc in known.items()}
    except Exception as exc:
        LOG.warning("Failed to load encodings: %s", exc)
        return {}


def scan_dataset(dataset_dir: Path, encodings_path: Path, save_encodings: bool = True):
    known_encodings = {}
    if not dataset_dir.exists() or not dataset_dir.is_dir():
        raise FileNotFoundError(f"Dataset directory not found: {dataset_dir}")

    for student_dir in sorted(dataset_dir.iterdir()):
        if not student_dir.is_dir() or student_dir.name.startswith('.'):
            continue

        student_name = normalize_name(student_dir.name)
        image_files = []
        for ext in ("*.jpg", "*.jpeg", "*.png"):
            image_files.extend(student_dir.glob(ext))

        if not image_files:
            LOG.warning("No images found for student: %s", student_name)
            continue

        embeddings = []
        for image_path in sorted(image_files)[:10]:
            try:
                image = face_recognition.load_image_file(str(image_path))
                locations = face_recognition.face_locations(image, model="hog")
                if len(locations) != 1:
                    LOG.debug("Skipping %s: found %d faces", image_path.name, len(locations))
                    continue
                encs = face_recognition.face_encodings(image, locations)
                if encs:
                    embeddings.append(np.asarray(encs[0], dtype=np.float32))
            except Exception as exc:
                LOG.debug("Skipping invalid image %s: %s", image_path.name, exc)
                continue

        if embeddings:
            avg_encoding = np.mean(embeddings, axis=0).astype(np.float32)
            known_encodings[student_name] = avg_encoding
            LOG.info("Student %s encoded from %d image(s)", student_name, len(embeddings))
        else:
            LOG.warning("No valid face encodings extracted for %s", student_name)

    if save_encodings and known_encodings:
        try:
            encodings_path.parent.mkdir(parents=True, exist_ok=True)
            with encodings_path.open("wb") as handle:
                pickle.dump({"encodings": known_encodings}, handle)
            LOG.info("Saved %d encodings to %s", len(known_encodings), encodings_path)
        except Exception as exc:
            LOG.warning("Unable to save encodings: %s", exc)

    return known_encodings


def match_face(encoding: np.ndarray, known_encodings: dict, threshold: float):
    if not known_encodings:
        return None, None, None

    names = list(known_encodings.keys())
    vectors = np.vstack([known_encodings[name] for name in names])
    distances = np.linalg.norm(vectors - encoding, axis=1)
    best_idx = int(np.argmin(distances))
    best_distance = float(distances[best_idx])
    if best_distance <= threshold:
        confidence = max(0.0, min(1.0, 1.0 - best_distance / threshold))
        return names[best_idx], best_distance, confidence
    return None, best_distance, 0.0


def api_mark_attendance(api_base: str, student_name: str, confidence: float, camera_name: str = "webcam"):
    payload = {
        "student_name": student_name,
        "confidence": confidence,
        "camera": camera_name,
    }
    url = api_base.rstrip("/") + "/api/mark_attendance"
    data = json.dumps(payload).encode("utf-8")
    headers = {"Content-Type": "application/json"}
    request = Request(url, data=data, headers=headers, method="POST")
    try:
        response = urlopen(request, timeout=10)
        body = response.read().decode("utf-8")
        LOG.info("Marked attendance for %s (confidence=%.2f)", student_name, confidence)
        return json.loads(body)
    except HTTPError as exc:
        LOG.warning("Attendance API error %s: %s", exc.code, exc.reason)
    except URLError as exc:
        LOG.warning("Attendance API unreachable: %s", exc)
    except Exception as exc:
        LOG.warning("Failed to call attendance API: %s", exc)
    return None


def draw_label(frame, location, label, color=(0, 255, 0)):
    top, right, bottom, left = location
    cv2.rectangle(frame, (left, top), (right, bottom), color, 2)
    text_size, _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
    text_w, text_h = text_size
    cv2.rectangle(frame, (left, top - text_h - 12), (left + text_w + 12, top), color, -1)
    cv2.putText(frame, label, (left + 6, top - 6), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)


def main():
    args = parse_args()
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )

    dataset_dir = Path(args.dataset)
    encodings_path = Path(args.encodings)

    known_encodings = load_encodings(encodings_path)
    if not known_encodings:
        LOG.info("Generating encodings from dataset: %s", dataset_dir)
        known_encodings = scan_dataset(dataset_dir, encodings_path, save_encodings=not args.no_save_encodings)

    if not known_encodings:
        LOG.error("No student encodings available. Please populate the dataset and retry.")
        return 1

    LOG.info("Starting webcam attendance. Recognizing %d students.", len(known_encodings))
    cap = cv2.VideoCapture(args.camera)
    if not cap.isOpened():
        LOG.error("Unable to open webcam index %s", args.camera)
        return 1

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, args.width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, args.height)

    cooldown = float(args.cooldown)
    last_marked = {}

    LOG.info("Press ESC to exit.")
    while True:
        ret, frame = cap.read()
        if not ret:
            LOG.warning("Unable to read frame from webcam")
            time.sleep(0.1)
            continue

        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        face_locations = face_recognition.face_locations(rgb_frame, model="hog")
        face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)

        for location, encoding in zip(face_locations, face_encodings):
            student_name, distance, confidence = match_face(encoding, known_encodings, args.threshold)
            label = "Unknown"
            box_color = (0, 0, 255)
            if student_name:
                label = f"{student_name} {confidence * 100:.0f}%"
                box_color = (0, 255, 0)
                now = time.time()
                last_time = last_marked.get(student_name, 0)
                if now - last_time >= cooldown:
                    api_mark_attendance(args.api_url, student_name, confidence, camera_name=f"camera-{args.camera}")
                    last_marked[student_name] = now
                else:
                    LOG.debug("Skipping duplicate mark for %s (cooldown %.1fs remaining)", student_name, cooldown - (now - last_time))
            draw_label(frame, location, label, color=box_color)

        footer = f"Students: {len(known_encodings)} | Cooldown: {cooldown}s | API: {args.api_url}"
        cv2.putText(frame, footer, (12, args.height - 16), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (240, 240, 240), 1)

        cv2.imshow("Camera Attendance", frame)
        if cv2.waitKey(1) & 0xFF == 27:
            break

    cap.release()
    cv2.destroyAllWindows()
    return 0


if __name__ == "__main__":
    sys.exit(main())
