from datetime import datetime, date
from sqlalchemy import Column, Integer, String, Float, DateTime, Date, UniqueConstraint

from .db import Base


class Student(Base):
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Student(id={self.id}, name='{self.name}')>"


class AttendanceLog(Base):
    __tablename__ = "attendance_logs"

    id = Column(Integer, primary_key=True, index=True)
    student_name = Column(String(255), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)
    confidence = Column(Float, nullable=False)

    __table_args__ = (
        UniqueConstraint("student_name", "date", name="uq_student_date"),
    )

    def __repr__(self):
        return (
            f"<AttendanceLog(id={self.id}, student='{self.student_name}', date={self.date})>"
        )
