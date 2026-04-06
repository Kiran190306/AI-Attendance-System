from datetime import date, datetime
from sqlalchemy.orm import Session

from .models import Student, AttendanceLog


class StudentRepository:
    @staticmethod
    def list_all(db: Session) -> list[Student]:
        return db.query(Student).order_by(Student.name).all()

    @staticmethod
    def get_by_name(db: Session, name: str) -> Student | None:
        return db.query(Student).filter(Student.name == name).first()

    @staticmethod
    def create(db: Session, name: str) -> Student:
        student = Student(name=name)
        db.add(student)
        db.commit()
        db.refresh(student)
        return student


class AttendanceRepository:
    @staticmethod
    def add_entry(db: Session, student_name: str, confidence: float) -> AttendanceLog | None:
        today = date.today()
        existing = (
            db.query(AttendanceLog)
            .filter(AttendanceLog.student_name == student_name, AttendanceLog.date == today)
            .first()
        )
        if existing:
            return existing
        entry = AttendanceLog(
            student_name=student_name,
            date=today,
            timestamp=datetime.utcnow(),
            confidence=confidence,
        )
        db.add(entry)
        db.commit()
        db.refresh(entry)
        return entry

    @staticmethod
    def list_all(db: Session) -> list[AttendanceLog]:
        return (
            db.query(AttendanceLog)
            .order_by(AttendanceLog.timestamp.desc())
            .all()
        )

    @staticmethod
    def list_today(db: Session) -> list[AttendanceLog]:
        today = date.today()
        return (
            db.query(AttendanceLog)
            .filter(AttendanceLog.date == today)
            .order_by(AttendanceLog.timestamp.desc())
            .all()
        )
