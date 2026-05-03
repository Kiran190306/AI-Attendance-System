from datetime import datetime, date
from sqlalchemy import Column, Integer, String, Float, DateTime, Date, UniqueConstraint, Index

from .db import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(255), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    __table_args__ = (
        Index('idx_users_username', 'username'),
        Index('idx_users_email', 'email'),
        Index('idx_users_created_at', 'created_at'),
    )

    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', email='{self.email}')>"


class Student(Base):
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    __table_args__ = (
        Index('idx_students_name', 'name'),
        Index('idx_students_created_at', 'created_at'),
    )

    def __repr__(self):
        return f"<Student(id={self.id}, name='{self.name}')>"


class AttendanceLog(Base):
    __tablename__ = "attendance_logs"

    id = Column(Integer, primary_key=True, index=True)
    student_name = Column(String(255), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    time = Column(String(16), nullable=True, index=False)
    camera = Column(String(255), nullable=True, index=True)
    confidence = Column(Float, nullable=False)

    __table_args__ = (
        UniqueConstraint("student_name", "date", name="uq_student_date"),
        Index('idx_attendance_student_name', 'student_name'),
        Index('idx_attendance_date', 'date'),
        Index('idx_attendance_timestamp', 'timestamp'),
        Index('idx_attendance_camera', 'camera'),
        Index('idx_attendance_student_date', 'student_name', 'date'),
    )

    def __repr__(self):
        return (
            f"<AttendanceLog(id={self.id}, student='{self.student_name}', date={self.date})>"
        )
