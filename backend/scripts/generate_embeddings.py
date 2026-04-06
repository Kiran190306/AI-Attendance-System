"""Initialize embeddings from dataset images and store in database."""
import asyncio
import logging
import sys
from pathlib import Path

# Add parent directories to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import numpy as np
from modules.recognition.embeddings_generator import EmbeddingsGenerator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# Import database and models
from app.database import Base
from app.models.student import Student
from app.config import get_settings

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

settings = get_settings()


async def generate_embeddings_for_dataset(
    dataset_path: Path = Path("dataset"),
    db_url: str | None = None,
) -> int:
    """
    Generate face embeddings from dataset and store in database.
    
    Returns:
        Number of students updated with embeddings
    """
    dataset_path = Path(dataset_path).resolve()
    
    if not dataset_path.exists():
        logger.error(f"Dataset path not found: {dataset_path}")
        return 0
    
    # Initialize embeddings generator
    try:
        generator = EmbeddingsGenerator(model="hog")
    except RuntimeError as e:
        logger.error(f"Failed to initialize generator: {e}")
        return 0
    
    logger.info(f"Generating embeddings from dataset: {dataset_path}")
    
    # Generate embeddings for all students
    embeddings_dict = generator.generate_embeddings_from_dataset(dataset_path)
    
    if not embeddings_dict:
        logger.warning("No embeddings generated from dataset")
        return 0
    
    logger.info(f"Generated embeddings for {len(embeddings_dict)} students")
    
    if generator.invalid_images:
        logger.warning(f"Skipped {len(generator.invalid_images)} invalid images:")
        for img in generator.invalid_images[:5]:
            logger.warning(f"  - {img}")
    
    # Connect to database and store embeddings
    db_url = db_url or str(settings.DATABASE_URL)
    engine = create_async_engine(db_url, echo=False)
    
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False, autoflush=False
    )
    
    updated_count = 0
    failed_count = 0
    
    try:
        async with async_session() as session:
            from sqlalchemy import select
            
            for student_name, embeddings in embeddings_dict.items():
                try:
                    # Query student by name (case-insensitive)
                    stmt = select(Student).where(
                        Student.full_name.ilike(f"%{student_name}%")
                    )
                    result = await session.execute(stmt)
                    student = result.scalars().first()
                    
                    if not student:
                        logger.warning(
                            f"No student found matching: {student_name}"
                        )
                        failed_count += 1
                        continue
                    
                    # Average embeddings and store
                    avg_embedding = generator.average_embeddings(embeddings)
                    student.set_embedding(avg_embedding, count=len(embeddings))
                    
                    logger.info(
                        f"Updated embeddings for {student.full_name} "
                        f"({len(embeddings)} source images)"
                    )
                    updated_count += 1
                    
                except Exception as e:
                    logger.error(f"Error processing {student_name}: {e}")
                    failed_count += 1
            
            # Commit all updates
            await session.commit()
    
    finally:
        await engine.dispose()
    
    logger.info(
        f"Completed: {updated_count} students updated, {failed_count} failed"
    )
    return updated_count


async def verify_embeddings(db_url: str | None = None) -> None:
    """Verify embeddings stored in database."""
    db_url = db_url or str(settings.DATABASE_URL)
    engine = create_async_engine(db_url, echo=False)
    
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False, autoflush=False
    )
    
    try:
        async with async_session() as session:
            from sqlalchemy import select
            
            stmt = select(Student).where(Student.face_embedding.isnot(None))
            result = await session.execute(stmt)
            students = result.scalars().all()
            
            logger.info(f"Verified {len(students)} students with embeddings:")
            for student in students:
                status = "✓" if student.has_valid_embedding() else "✗"
                logger.info(
                    f"  {status} {student.full_name} "
                    f"({student.embeddings_count} source images)"
                )
    
    finally:
        await engine.dispose()


async def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Generate face embeddings from dataset and store in database"
    )
    parser.add_argument(
        "-d", "--dataset",
        type=Path,
        default=Path("dataset"),
        help="Path to dataset directory (default: dataset/)"
    )
    parser.add_argument(
        "--db-url",
        type=str,
        default=None,
        help="Database URL (default: from settings)"
    )
    parser.add_argument(
        "--verify",
        action="store_true",
        help="Verify embeddings after generation"
    )
    
    args = parser.parse_args()
    
    logger.info("Starting embeddings generation...")
    updated = await generate_embeddings_for_dataset(
        dataset_path=args.dataset,
        db_url=args.db_url,
    )
    
    if args.verify and updated > 0:
        logger.info("Verifying embeddings...")
        await verify_embeddings(db_url=args.db_url)
    
    logger.info("Done!")
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
