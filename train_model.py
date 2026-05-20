#!/usr/bin/env python3
"""
Face Model Training Script
Train the face recognition model from dataset
"""

import sys
import logging
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from backend.core.face_trainer import FaceTrainer

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(name)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Train the model"""
    print("=" * 70)
    print("Face Recognition Model Training")
    print("=" * 70)
    
    # Create trainer
    trainer = FaceTrainer()
    
    # Train from dataset
    print("\n✓ Training from dataset...")
    stats = trainer.train_from_dataset()
    
    print("\n✓ Training Results:")
    print(f"  - Students trained: {stats['trained']}")
    print(f"  - Students skipped: {stats['skipped']}")
    print(f"  - Students failed: {stats['failed']}")
    print(f"  - Student list: {', '.join(stats['students']) if stats['students'] else 'None'}")
    
    # Get final stats
    final_stats = trainer.get_stats()
    print(f"\n✓ Total trained students: {final_stats['total_students']}")
    
    print("\n" + "=" * 70)
    if stats['trained'] > 0:
        print("✅ Model training completed successfully!")
        print(f"Encodings saved to: {trainer.ENCODINGS_FILE}")
        return 0
    else:
        print("⚠️  No students were trained. Check dataset structure.")
        print(f"Expected structure: {trainer.DATASET_PATH}/{{student_name}}/{{image.jpg}}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
