"""Helper script for creating test dataset from webcam."""
import cv2
import argparse
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def capture_training_images(
    student_name: str,
    num_images: int = 10,
    dataset_root: Path = Path("dataset"),
) -> bool:
    """
    Capture images from webcam for a student.
    
    Usage:
        python scripts/capture_training_images.py "John Doe" --num 10
    
    Instructions for user:
        1. Face the webcam
        2. Press SPACE to capture image
        3. Repeat from different angles/distances
        4. Press Q when done
    """
    dataset_root = Path(dataset_root)
    student_dir = dataset_root / student_name
    student_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Capturing images for: {student_name}")
    logger.info(f"Save directory: {student_dir}")
    logger.info(f"Target images: {num_images}")
    
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        logger.error("Cannot open webcam")
        return False
    
    # Set camera resolution
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
    
    logger.info("\n" + "="*50)
    logger.info("INSTRUCTIONS:")
    logger.info("  - Position face in center of frame")
    logger.info("  - Press SPACE to capture")
    logger.info("  - Capture from multiple angles")
    logger.info("  - Press Q when done")
    logger.info("="*50 + "\n")
    
    captured = 0
    
    try:
        while captured < num_images:
            ret, frame = cap.read()
            if not ret:
                break
            
            # Add text overlay
            h, w = frame.shape[:2]
            cv2.putText(
                frame,
                f"Captured: {captured}/{num_images}",
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 0), 2
            )
            cv2.putText(
                frame,
                "SPACE: capture | Q: done",
                (10, h - 20),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 1
            )
            
            # Draw center crosshair
            cv2.line(frame, (w//2 - 20, h//2), (w//2 + 20, h//2), (0, 255, 255), 2)
            cv2.line(frame, (w//2, h//2 - 20), (w//2, h//2 + 20), (0, 255, 255), 2)
            
            cv2.imshow("Capture Training Images", frame)
            
            key = cv2.waitKey(1) & 0xFF
            
            if key == ord(' '):
                # Save image
                image_path = student_dir / f"face_{captured+1:03d}.jpg"
                cv2.imwrite(str(image_path), frame)
                captured += 1
                logger.info(f"Captured: {image_path.name}")
            
            elif key == ord('q'):
                break
    
    finally:
        cap.release()
        cv2.destroyAllWindows()
    
    logger.info(f"\nCapture complete: {captured} images saved")
    return captured > 0


def main():
    parser = argparse.ArgumentParser(
        description="Capture training images from webcam for face recognition"
    )
    parser.add_argument(
        "student_name",
        type=str,
        help="Student name (directory will be created in dataset/)"
    )
    parser.add_argument(
        "--num",
        type=int,
        default=10,
        help="Number of images to capture (default: 10)"
    )
    parser.add_argument(
        "--dataset",
        type=Path,
        default=Path("../dataset"),
        help="Dataset root directory (default: ../dataset/)"
    )
    
    args = parser.parse_args()
    
    success = capture_training_images(
        args.student_name,
        num_images=args.num,
        dataset_root=args.dataset,
    )
    
    return 0 if success else 1


if __name__ == "__main__":
    import sys
    exit_code = main()
    sys.exit(exit_code)
