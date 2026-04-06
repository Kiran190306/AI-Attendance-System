from __future__ import annotations

import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from collections import defaultdict

import numpy as np

try:
    import face_recognition
except ImportError:  # pragma: no cover - runtime dependency
    face_recognition = None  # type: ignore

from . import config, utils

logger = logging.getLogger(__name__)


class DatasetLoaderError(Exception):
    """Raised when dataset cannot be loaded or is invalid."""


class DatasetLoader:
    """Automatic dataset scanner for face recognition.

    Scans dataset folder structure, loads student images, computes face encodings.

    The dataset structure is expected to be::

        dataset/
            Student Name 1/
                face_001.jpg
                face_002.png
                other_001.jpg (ignored if no face)
            Student Name 2/
                face_*.jpg/png/jpeg
                ...

    Features:
    - Automatically discovers student folders
    - Loads images & extracts face encodings
    - Ignores images with 0 or >1 faces
    - Computes averaged embeddings per student
    - Detailed logging and statistics
    - Comprehensive error handling
    """

    def __init__(self, dataset_path: Path | str = config.DATASET_PATH) -> None:
        self.dataset_path = Path(dataset_path)
        utils.ensure_dataset_exists(self.dataset_path)

        if face_recognition is None:
            raise RuntimeError("face_recognition library is required")

        # Statistics tracking
        self._stats = {
            "total_students": 0,
            "total_images_found": 0,
            "total_images_processed": 0,
            "total_images_skipped": 0,
            "students_with_valid_faces": 0,
            "students_with_no_faces": 0,
        }

        self._per_student_stats: Dict[str, Dict] = {}

    # ------------------------------------------------------------------
    # public API
    # ------------------------------------------------------------------

    def load_embeddings(self) -> Dict[str, np.ndarray]:
        """Scan dataset and compute face embeddings for each student.

        Returns:
            Dict mapping student name -> averaged embedding (128-d)

        Raises:
            DatasetLoaderError: If dataset path invalid or no students found
        """
        if not self.dataset_path.exists():
            raise DatasetLoaderError(f"Dataset path not found: {self.dataset_path}")

        # Discover student folders
        student_dirs = self._get_student_directories()

        if not student_dirs:
            raise DatasetLoaderError("No student folders found in dataset")

        self._stats["total_students"] = len(student_dirs)
        logger.info(
            "starting dataset scan: %d student(s) found", self._stats["total_students"]
        )

        embeddings: Dict[str, np.ndarray] = {}

        for student_dir in sorted(student_dirs):
            name = student_dir.name
            embedding = self._process_student_directory(student_dir)

            if embedding is not None:
                embeddings[name] = embedding
                self._stats["students_with_valid_faces"] += 1
            else:
                self._stats["students_with_no_faces"] += 1
                logger.warning(
                    "student '%s' had no valid face images (skipped)", name
                )

        # Log comprehensive summary
        self._log_summary()

        return embeddings

    def get_statistics(self) -> Dict:
        """Return dataset loading statistics."""
        return {
            "total_students": self._stats["total_students"],
            "total_images_found": self._stats["total_images_found"],
            "total_images_processed": self._stats["total_images_processed"],
            "total_images_skipped": self._stats["total_images_skipped"],
            "students_with_valid_faces": self._stats["students_with_valid_faces"],
            "students_with_no_faces": self._stats["students_with_no_faces"],
            "per_student": self._per_student_stats,
        }

    def get_student_list(self) -> List[str]:
        """Return sorted list of all student directories."""
        return sorted([d.name for d in self._get_student_directories()])

    # ------------------------------------------------------------------
    # internal helpers
    # ------------------------------------------------------------------

    def _get_student_directories(self) -> List[Path]:
        """Get all non-hidden student directories."""
        return [
            d
            for d in self.dataset_path.iterdir()
            if d.is_dir() and not d.name.startswith(".")
        ]

    def _get_image_files(self, student_dir: Path) -> List[Path]:
        """Find all image files in student directory."""
        extensions = ["jpg", "jpeg", "png", "JPG", "JPEG", "PNG"]
        images = []
        for ext in extensions:
            images.extend(student_dir.glob(f"*.{ext}"))
        return images

    def _process_student_directory(
        self, student_dir: Path
    ) -> Optional[np.ndarray]:
        """Process one student directory and return averaged embedding.

        Returns:
            Averaged embedding (128-d) or None if no valid faces
        """
        name = student_dir.name
        logger.info("processing student: %s", name)

        # Find all images
        images = self._get_image_files(student_dir)
        self._stats["total_images_found"] += len(images)

        if not images:
            logger.warning("  no image files found in %s", student_dir)
            self._per_student_stats[name] = {
                "images_found": 0,
                "images_processed": 0,
                "images_skipped": 0,
                "reason": "no_images",
            }
            return None

        logger.debug("  found %d image(s)", len(images))

        # Process up to 10 images per student (performance limit)
        vectors: List[np.ndarray] = []
        skipped = 0

        for image_path in images[:10]:
            try:
                img = face_recognition.load_image_file(str(image_path))
                face_locs = face_recognition.face_locations(img, model="hog")

                # Strict: exactly one face per image
                if len(face_locs) == 0:
                    logger.debug("  %s: no face detected", image_path.name)
                    skipped += 1
                    continue
                elif len(face_locs) > 1:
                    logger.debug(
                        "  %s: %d faces found (expected 1)", image_path.name, len(face_locs)
                    )
                    skipped += 1
                    continue

                # Extract encoding
                encodings = face_recognition.face_encodings(img, face_locs)
                if encodings:
                    vectors.append(np.array(encodings[0], dtype=np.float32))
                    logger.debug("  %s: face encoding extracted", image_path.name)
                else:
                    logger.debug("  %s: could not extract encoding", image_path.name)
                    skipped += 1

            except Exception as exc:
                logger.debug("  %s: error — %s", image_path.name, exc)
                skipped += 1
                continue

        # Track statistics
        processed = len(vectors)
        self._stats["total_images_processed"] += processed
        self._stats["total_images_skipped"] += skipped

        self._per_student_stats[name] = {
            "images_found": len(images),
            "images_processed": processed,
            "images_skipped": skipped,
            "reason": "success" if vectors else "no_valid_faces",
        }

        if not vectors:
            logger.warning("  %s: no valid face encodings extracted", name)
            return None

        # Compute averaged embedding
        avg_embedding = np.mean(vectors, axis=0, dtype=np.float32)
        logger.info(
            "  %s: loaded %d valid encoding(s), created averaged embedding", name, len(vectors)
        )

        return avg_embedding

    def _log_summary(self) -> None:
        """Log comprehensive summary after dataset load."""
        logger.info("=" * 70)
        logger.info("DATASET LOAD SUMMARY")
        logger.info("=" * 70)
        logger.info("Dataset Path:          %s", self.dataset_path.resolve())
        logger.info("Total Students:        %d", self._stats["total_students"])
        logger.info("  - With valid faces:  %d", self._stats["students_with_valid_faces"])
        logger.info("  - No valid faces:    %d", self._stats["students_with_no_faces"])
        logger.info("Total Images Found:    %d", self._stats["total_images_found"])
        logger.info("  - Processed:         %d", self._stats["total_images_processed"])
        logger.info("  - Skipped:           %d", self._stats["total_images_skipped"])

        if self._stats["total_images_found"] > 0:
            process_rate = (
                self._stats["total_images_processed"] / self._stats["total_images_found"] * 100
            )
            logger.info("Process Rate:          %.1f%%", process_rate)

        # Log warnings for problematic students
        problem_students = [
            (name, stat)
            for name, stat in self._per_student_stats.items()
            if stat["reason"] != "success"
        ]

        if problem_students:
            logger.warning("Students with issues:")
            for name, stat in problem_students:
                logger.warning(
                    "  - %s: %s (found=%d, processed=%d, skipped=%d)",
                    name,
                    stat["reason"].replace("_", " ").title(),
                    stat["images_found"],
                    stat["images_processed"],
                    stat["images_skipped"],
                )

        logger.info("=" * 70)
