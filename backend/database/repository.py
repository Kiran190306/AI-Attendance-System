from datetime import date, datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc

from .models import Student, AttendanceLog


class StudentRepository:
    @staticmethod
    def list_all(db: Session) -> list[Student]:
        """Get all students ordered by name. Indexed on name."""
        return db.query(Student).order_by(Student.name).all()

    @staticmethod
    def get_by_name(db: Session, name: str) -> Student | None:
        """Get student by name. Indexed for fast lookup."""
        return db.query(Student).filter(Student.name == name).first()

    @staticmethod
    def create(db: Session, name: str) -> Student:
        """Create new student."""
        student = Student(name=name)
        db.add(student)
        db.commit()
        db.refresh(student)
        return student


class AttendanceRepository:
    @staticmethod
    def add_entry(db: Session, student_name: str, confidence: float, timestamp: datetime | None = None, camera: str | None = None) -> AttendanceLog | None:
        """Add attendance entry if not already marked for the date (prevents duplicates).
        timestamp and camera are optional and stored if provided."""
        if timestamp is None:
            timestamp = datetime.utcnow()
        entry_date = timestamp.date()
        # Check for existing entry using compound index (student_name, date)
        existing = (
            db.query(AttendanceLog)
            .filter(
                and_(
                    AttendanceLog.student_name == student_name,
                    AttendanceLog.date == entry_date
                )
            )
            .first()
        )
        if existing:
            return existing

        entry = AttendanceLog(
            student_name=student_name,
            date=entry_date,
            timestamp=timestamp,
            time=timestamp.strftime("%H:%M:%S"),
            camera=camera,
            confidence=confidence,
        )
        db.add(entry)
        db.commit()
        db.refresh(entry)
        return entry

    @staticmethod
    def list_all(db: Session) -> list[AttendanceLog]:
        """Get all attendance records sorted by timestamp descending. Uses timestamp index."""
        return (
            db.query(AttendanceLog)
            .order_by(desc(AttendanceLog.timestamp))
            .all()
        )

    @staticmethod
    def list_today(db: Session) -> list[AttendanceLog]:
        """Get today's attendance records. Uses date index."""
        today = date.today()
        return (
            db.query(AttendanceLog)
            .filter(AttendanceLog.date == today)
            .order_by(desc(AttendanceLog.timestamp))
            .all()
        )
    
    @staticmethod
    def list_by_date_range(db: Session, start_date: date, end_date: date) -> list[AttendanceLog]:
        """Get attendance records for a date range. Uses date index."""
        return (
            db.query(AttendanceLog)
            .filter(
                and_(
                    AttendanceLog.date >= start_date,
                    AttendanceLog.date <= end_date
                )
            )
            .order_by(desc(AttendanceLog.date), desc(AttendanceLog.timestamp))
            .all()
        )
    
    @staticmethod
    def get_by_student_and_date(db: Session, student_name: str, query_date: date) -> AttendanceLog | None:
        """Get specific attendance record. Uses composite index (student_name, date)."""
        return (
            db.query(AttendanceLog)
            .filter(
                and_(
                    AttendanceLog.student_name == student_name,
                    AttendanceLog.date == query_date
                )
            )
            .first()
        )
