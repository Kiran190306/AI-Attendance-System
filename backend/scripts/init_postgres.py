#!/usr/bin/env python3
"""
Initialize PostgreSQL database for AI Attendance System.

This script:
1. Creates database schema (tables with indexes)
2. Creates default admin user
3. Sets up connection pooling

Usage:
    python backend/scripts/init_postgres.py
    
    With custom DATABASE_URL:
    DATABASE_URL=postgresql://user:pass@localhost:5432/ai_attendance python backend/scripts/init_postgres.py
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.database.db import init_db, engine
from backend.database.models import User
from backend.services.user_service import get_password_hash
from backend.database.db import SessionLocal
import logging

logger = logging.getLogger(__name__)


def check_database_connection():
    """Test PostgreSQL connection."""
    try:
        with engine.connect() as conn:
            result = conn.execute("SELECT 1")
            logger.info("PostgreSQL connection successful")
            return True
    except Exception as e:
        logger.exception("PostgreSQL connection failed: %s", e)
        return False


def create_tables():
    """Create all database tables with indexes."""
    try:
        init_db()
        logger.info("Database tables created successfully")
        return True
    except Exception as e:
        logger.exception("Failed to create tables: %s", e)
        return False


def create_admin_user():
    """Create default admin user if it doesn't exist."""
    db = SessionLocal()
        try:
            # Check if admin already exists
            admin = db.query(User).filter(User.username == "admin").first()
            if admin:
                logger.info("Admin user already exists")
                return True
            
            # Create admin user
            admin_user = User(
                username="admin",
                email="admin@attendance.local",
                hashed_password=get_password_hash("admin123")
            )
            db.add(admin_user)
            db.commit()
            logger.info("Admin user created (username: admin)")
            logger.warning("Default admin password was set; change immediately in production")
            return True
        except Exception as e:
            logger.exception("Failed to create admin user: %s", e)
            db.rollback()
            return False
        finally:
            db.close()


def print_database_info():
    """Print database information."""
    db_url = os.getenv("DATABASE_URL", "Not set")
    logger.info("PostgreSQL Database Configuration")
    logger.info("DATABASE_URL: %s", db_url)
    logger.info("Database Tables Created: users, students, attendance_logs")
    logger.info("Indexes: users(username,email,created_at), students(name), attendance_logs(student_name,date)")


def main():
    """Main initialization function."""
    logger.info("PostgreSQL Database Initialization starting")
    # Step 1: Check connection
    logger.info("[1/4] Checking PostgreSQL connection...")
    if not check_database_connection():
        logger.error("Failed to connect to PostgreSQL. Ensure DATABASE_URL is correct.")
        sys.exit(1)

    # Step 2: Create tables
    logger.info("[2/4] Creating database tables...")
    if not create_tables():
        logger.error("Failed to create tables.")
        sys.exit(1)

    # Step 3: Create admin user
    logger.info("[3/4] Setting up admin user...")
    create_admin_user()

    # Step 4: Print info
    logger.info("[4/4] Configuration summary...")
    print_database_info()

    logger.info("PostgreSQL initialization complete")
    logger.info("Next steps: update DATABASE_URL in .env if needed and start backend with gunicorn")


if __name__ == "__main__":
    main()
