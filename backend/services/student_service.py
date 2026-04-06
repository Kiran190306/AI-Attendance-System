from typing import List
from pathlib import Path

from ..database.db import SessionLocal
from ..database.repository import StudentRepository
from ..utils import helpers
from ..config import DATASET_PATH


class StudentServiceError(Exception):
    pass


class StudentService:
    def __init__(self):
        pass

    def list_students(self) -> List[str]:
        db = SessionLocal()
        try:
            students = StudentRepository.list_all(db)
            return [s.name for s in students]
        finally:
            db.close()

    def add_student(self, name: str) -> str:
        norm = helpers.normalize_student_name(name)
        if not norm:
            raise StudentServiceError("Invalid student name")
        # create dataset directory if missing
        dataset_dir = Path(DATASET_PATH) / norm
        dataset_dir.mkdir(parents=True, exist_ok=True)
        # add to db if not present
        db = SessionLocal()
        try:
            existing = StudentRepository.get_by_name(db, norm)
            if existing:
                return existing.name
            StudentRepository.create(db, norm)
            return norm
        finally:
            db.close()
