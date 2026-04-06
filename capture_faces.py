#!/usr/bin/env python3
"""
Capture face images for training the face recognition system.

Usage:
    python capture_faces.py

Controls:
    S - Save frame (space bar)
    Q - Quit (ESC)
    C - Clear last frame (C)
"""
import os
import sys
import cv2
import numpy as np
from pathlib import Path
from datetime import datetime


def main():
    """Main capture loop."""
    print("=" * 60)
    print("AI Attendance System - Face Capture Tool")
    print("=" * 60)

    # Get student name
    student_name = input("\nEnter student name: ").strip()
    if not student_name:
        print("Error: Student name cannot be empty")
        return

    # Create dataset directory
    dataset_dir = Path("dataset") / student_name
    dataset_dir.mkdir(parents=True, exist_ok=True)

    print(f"\nDataset directory: {dataset_dir}")
    print(f"Existing images: {len(list(dataset_dir.glob('*.jpg')))}")

    # Open camera
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Error: Cannot open camera")
        return

    print("\n" + "=" * 60)
    print("Camera Ready")
    print("=" * 60)
    print("Press 'S' or SPACE to capture image")
    print("Press 'C' to clear last frame preview")
    print("Press 'Q' or ESC to quit")
    print("=" * 60 + "\n")

    frame_count = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            print("Error: Cannot read frame")
            break

        # Flip frame for mirror effect
        frame = cv2.flip(frame, 1)

        # Display current frame
        cv2.imshow(f'Capturing faces for: {student_name}', frame)

        # Handle key presses
        key = cv2.waitKey(1) & 0xFF

        if key == ord('s') or key == ord('S') or key == 32:  # 's', 'S', or SPACE
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{student_name}_{timestamp}.jpg"
            filepath = dataset_dir / filename

            cv2.imwrite(str(filepath), frame)
            frame_count += 1
            print(f"✓ Saved: {filename} (Total: {frame_count})")

        elif key == ord('c') or key == ord('C'):  # 'C'
            print("Frame preview cleared")

        elif key == ord('q') or key == ord('Q') or key == 27:  # 'q', 'Q', or ESC
            print("\nExiting capture mode...")
            break

    cap.release()
    cv2.destroyAllWindows()

    print(f"\n{'=' * 60}")
    print(f"Capture Complete")
    print(f"{'=' * 60}")
    print(f"Student: {student_name}")
    print(f"Total images captured: {frame_count}")
    print(f"Saved to: {dataset_dir}")
    print(f"{'=' * 60}\n")

    if frame_count > 0:
        print("✓ Ready to train the model!")
    else:
        print("⚠ No images captured. Please try again.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\nError: {e}")
        sys.exit(1)

