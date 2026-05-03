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


def check_database_connection():
    """Test PostgreSQL connection."""
    try:
        with engine.connect() as conn:
            result = conn.execute("SELECT 1")
            print("✓ PostgreSQL connection successful")
            return True
    except Exception as e:
        print(f"✗ PostgreSQL connection failed: {e}")
        return False


def create_tables():
    """Create all database tables with indexes."""
    try:
        init_db()
        print("✓ Database tables created successfully")
        return True
    except Exception as e:
        print(f"✗ Failed to create tables: {e}")
        return False


def create_admin_user():
    """Create default admin user if it doesn't exist."""
    db = SessionLocal()
    try:
        # Check if admin already exists
        admin = db.query(User).filter(User.username == "admin").first()
        if admin:
            print("✓ Admin user already exists")
            return True
        
        # Create admin user
        admin_user = User(
            username="admin",
            email="admin@attendance.local",
            hashed_password=get_password_hash("admin123")
        )
        db.add(admin_user)
        db.commit()
        print("✓ Admin user created (username: admin, password: admin123)")
        print("  ⚠ Change password immediately in production!")
        return True
    except Exception as e:
        print(f"✗ Failed to create admin user: {e}")
        db.rollback()
        return False
    finally:
        db.close()


def print_database_info():
    """Print database information."""
    db_url = os.getenv("DATABASE_URL", "Not set")
    print("\n" + "="*60)
    print("PostgreSQL Database Configuration")
    print("="*60)
    print(f"DATABASE_URL: {db_url}")
    print("\nDatabase Tables Created:")
    print("  - users (id, username, email, hashed_password, created_at)")
    print("  - students (id, name, created_at)")
    print("  - attendance_logs (id, student_name, date, timestamp, confidence)")
    print("\nIndexes for Performance:")
    print("  - users: username, email, created_at")
    print("  - students: name, created_at")
    print("  - attendance_logs: student_name, date, timestamp, (student_name, date)")
    print("="*60 + "\n")


def main():
    """Main initialization function."""
    print("=" * 60)
    print("PostgreSQL Database Initialization")
    print("=" * 60 + "\n")
    
    # Step 1: Check connection
    print("[1/4] Checking PostgreSQL connection...")
    if not check_database_connection():
        print("\nFailed to connect to PostgreSQL.")
        print("Ensure PostgreSQL is running and DATABASE_URL is correct.")
        sys.exit(1)
    print()
    
    # Step 2: Create tables
    print("[2/4] Creating database tables...")
    if not create_tables():
        print("\nFailed to create tables.")
        sys.exit(1)
    print()
    
    # Step 3: Create admin user
    print("[3/4] Setting up admin user...")
    create_admin_user()
    print()
    
    # Step 4: Print info
    print("[4/4] Configuration summary...")
    print_database_info()
    
    print("✓ PostgreSQL initialization complete!")
    print("\nNext steps:")
    print("  1. Update DATABASE_URL in .env if needed")
    print("  2. Start backend server: python -m backend.app")
    print("  3. API documentation available at http://localhost:5000/api/docs")


if __name__ == "__main__":
    main()
