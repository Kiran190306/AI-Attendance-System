from sqlalchemy import create_engine, event, inspect, text
from sqlalchemy.orm import sessionmaker, declarative_base

from ..config import DATABASE_URL
import csv
from pathlib import Path
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

# Create engine with appropriate settings for PostgreSQL
engine = create_engine(
    DATABASE_URL,
    echo=False,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,  # Verify connection before using
)

# Enable connection pooling for PostgreSQL
@event.listens_for(engine, "connect")
def receive_connect(dbapi_conn, connection_record):
    """Configure PostgreSQL connection settings."""
    pass  # psycopg2 handles this automatically

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

Base = declarative_base()


def _ensure_attendance_schema():
    from .models import AttendanceLog

    inspector = inspect(engine)
    if AttendanceLog.__tablename__ not in inspector.get_table_names():
        return

    columns = {col["name"] for col in inspector.get_columns(AttendanceLog.__tablename__)}
    with engine.connect() as conn:
        if "time" not in columns:
            if engine.dialect.name == "sqlite":
                conn.execute(text('ALTER TABLE attendance_logs ADD COLUMN "time" VARCHAR(16)'))
            else:
                conn.execute(text('ALTER TABLE attendance_logs ADD COLUMN IF NOT EXISTS "time" VARCHAR(16)'))
            logger.info("Added missing attendance_logs.time column")
        if "camera" not in columns:
            if engine.dialect.name == "sqlite":
                conn.execute(text('ALTER TABLE attendance_logs ADD COLUMN camera VARCHAR(255)'))
            else:
                conn.execute(text('ALTER TABLE attendance_logs ADD COLUMN IF NOT EXISTS camera VARCHAR(255)'))
            logger.info("Added missing attendance_logs.camera column")


def init_db():
    """Create all tables in the database."""
    from . import models  # ensure models are imported

    Base.metadata.create_all(bind=engine)
    _ensure_attendance_schema()
    # Seed sample attendance records and CSV if no attendance exists
    db = None
    try:
        from .models import AttendanceLog
        db = SessionLocal()
        count = db.query(AttendanceLog).count()
        if count == 0:
            now = datetime.utcnow()
            sample = [
                ("Alice Smith", now - timedelta(minutes=10), 0.95, "Camera 1"),
                ("Bob Johnson", now - timedelta(minutes=8), 0.92, "Camera 1"),
                ("Carol Lee", now - timedelta(minutes=6), 0.88, "Camera 2"),
                ("David Kim", now - timedelta(minutes=4), 0.91, "Camera 2"),
                ("Eve Martinez", now - timedelta(minutes=2), 0.89, "Camera 3"),
            ]
            for name, ts, conf, camera in sample:
                entry = AttendanceLog(
                    student_name=name,
                    date=ts.date(),
                    timestamp=ts,
                    confidence=conf,
                )
                db.add(entry)
            db.commit()
            # ensure CSV exists and write sample rows
            csv_path = Path("attendance/attendance.csv")
            csv_path.parent.mkdir(parents=True, exist_ok=True)
            with open(csv_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(
                    f,
                    fieldnames=["date", "time", "name", "timestamp_iso", "confidence", "camera_id", "camera_name"],
                )
                writer.writeheader()
                for name, ts, conf, camera in sample:
                    writer.writerow({
                        "date": ts.date().isoformat(),
                        "time": ts.strftime("%H:%M:%S"),
                        "name": name,
                        "timestamp_iso": ts.isoformat(),
                        "confidence": f"{conf:.2%}",
                        "camera_id": "",
                        "camera_name": camera,
                    })
            logger.info("Seeded sample attendance records into DB and CSV")
    except Exception as exc:
        try:
            logger.warning(f"Could not seed initial attendance data: {exc}")
        except Exception:
            pass
    finally:
        if db:
            db.close()
