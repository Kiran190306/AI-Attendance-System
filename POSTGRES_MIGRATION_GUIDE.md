# PostgreSQL Migration Guide

## Overview

This guide covers upgrading the AI Attendance System from SQLite to PostgreSQL.

## Prerequisites

- PostgreSQL 12 or higher installed
- Python 3.9+
- pip package manager

## Installation Steps

### 1. Install PostgreSQL

#### Windows
```bash
# Download from https://www.postgresql.org/download/windows/
# Or use Chocolatey:
choco install postgresql14
```

#### macOS
```bash
# Using Homebrew:
brew install postgresql
brew services start postgresql
```

#### Linux (Ubuntu/Debian)
```bash
sudo apt-get update
sudo apt-get install postgresql postgresql-contrib
sudo systemctl start postgresql
```

### 2. Create PostgreSQL User and Database

```bash
# Login to PostgreSQL
psql -U postgres

# Create database user
CREATE USER attendance_user WITH PASSWORD 'secure_password_here';

# Create database
CREATE DATABASE ai_attendance OWNER attendance_user;

# Grant privileges
GRANT ALL PRIVILEGES ON DATABASE ai_attendance TO attendance_user;
\c ai_attendance
GRANT ALL PRIVILEGES ON SCHEMA public TO attendance_user;

# Exit psql
\q
```

### 3. Update Requirements

```bash
cd backend
pip install -r requirements.txt
```

Key packages:
- `psycopg2-binary>=2.9.9` - PostgreSQL adapter for Python
- `sqlalchemy>=2.0.25` - ORM and database toolkit

### 4. Configure Environment Variables

Create `.env` file in project root:

```bash
# PostgreSQL Connection
DATABASE_URL=postgresql://attendance_user:secure_password_here@localhost:5432/ai_attendance

# Or for production (using environment variable):
# DATABASE_URL=postgresql://user:pass@remote-host:5432/ai_attendance
```

### 5. Initialize Database

```bash
cd d:\AI-Attendance-System

# Initialize tables and indexes
python backend/scripts/init_postgres.py
```

Expected output:
```
====================================================
PostgreSQL Database Initialization
====================================================

[1/4] Checking PostgreSQL connection...
✓ PostgreSQL connection successful

[2/4] Creating database tables...
✓ Database tables created successfully

[3/4] Setting up admin user...
✓ Admin user created (username: admin, password: admin123)
  ⚠ Change password immediately in production!

[4/4] Configuration summary...
====================================================
PostgreSQL Database Configuration
====================================================
DATABASE_URL: postgresql://attendance_user:secure_password_here@localhost:5432/ai_attendance

Database Tables Created:
  - users (id, username, email, hashed_password, created_at)
  - students (id, name, created_at)
  - attendance_logs (id, student_name, date, timestamp, confidence)

Indexes for Performance:
  - users: username, email, created_at
  - students: name, created_at
  - attendance_logs: student_name, date, timestamp, (student_name, date)
====================================================

✓ PostgreSQL initialization complete!
```

## Database Schema

### users Table
```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(255) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for fast lookups
CREATE INDEX idx_users_username ON users (username);
CREATE INDEX idx_users_email ON users (email);
CREATE INDEX idx_users_created_at ON users (created_at);
```

### students Table
```sql
CREATE TABLE students (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX idx_students_name ON students (name);
CREATE INDEX idx_students_created_at ON students (created_at);
```

### attendance_logs Table
```sql
CREATE TABLE attendance_logs (
    id SERIAL PRIMARY KEY,
    student_name VARCHAR(255) NOT NULL,
    date DATE NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    confidence FLOAT NOT NULL,
    UNIQUE (student_name, date)
);

-- Indexes for common queries
CREATE INDEX idx_attendance_student_name ON attendance_logs (student_name);
CREATE INDEX idx_attendance_date ON attendance_logs (date);
CREATE INDEX idx_attendance_timestamp ON attendance_logs (timestamp DESC);
CREATE INDEX idx_attendance_student_date ON attendance_logs (student_name, date);
```

## Performance Optimizations

### Indexes Used

1. **users table**
   - `username` - O(log N) lookup for authentication
   - `email` - O(log N) lookup for email verification
   - `created_at` - Quick filtering by registration time

2. **students table**
   - `name` - O(log N) lookup by student name
   - `created_at` - Track enrollment dates

3. **attendance_logs table**
   - `student_name` - Find all records for a student
   - `date` - Filter by attendance date
   - `timestamp` - Sort most recent entries first (DESC)
   - `(student_name, date)` - Composite index for unique constraint and queries

### Query Optimization

All repository methods use indexed columns:

```python
# Fast: Uses composite index (student_name, date)
db.query(AttendanceLog).filter(
    and_(
        AttendanceLog.student_name == "John",
        AttendanceLog.date == today
    )
).first()

# Fast: Uses date index
db.query(AttendanceLog).filter(
    AttendanceLog.date == today
).all()

# Fast: Uses timestamp index (DESC)
db.query(AttendanceLog).order_by(
    desc(AttendanceLog.timestamp)
).all()
```

### Connection Pooling

PostgreSQL settings in `backend/database/db.py`:

```python
engine = create_engine(
    DATABASE_URL,
    echo=False,
    pool_size=10,           # Number of connections to keep in pool
    max_overflow=20,        # Additional connections when pool exhausted
    pool_pre_ping=True,     # Verify connection before using
)
```

This ensures:
- ✓ Connections reused efficiently
- ✓ Stale connections detected and replaced
- ✓ Better performance under load

## Migration from SQLite

If migrating from existing SQLite database:

### 1. Export data from SQLite
```bash
cd d:\AI-Attendance-System

# Export users table
sqlite3 attendance.db "SELECT * FROM users;" > users.csv

# Export students table
sqlite3 attendance.db "SELECT * FROM students;" > students.csv

# Export attendance_logs
sqlite3 attendance.db "SELECT * FROM attendance_logs;" > attendance_logs.csv
```

### 2. Import to PostgreSQL
```bash
# Copy CSV files to PostgreSQL
psql -U attendance_user -d ai_attendance -c \
  "COPY users FROM '/path/to/users.csv' WITH (FORMAT csv)"

psql -U attendance_user -d ai_attendance -c \
  "COPY students FROM '/path/to/students.csv' WITH (FORMAT csv)"

psql -U attendance_user -d ai_attendance -c \
  "COPY attendance_logs FROM '/path/to/attendance_logs.csv' WITH (FORMAT csv)"
```

### 3. Verify data
```bash
psql -U attendance_user -d ai_attendance

# Check counts
SELECT COUNT(*) FROM users;
SELECT COUNT(*) FROM students;
SELECT COUNT(*) FROM attendance_logs;

\q
```

## Troubleshooting

### Connection Error: "could not connect to server"
- Check PostgreSQL is running: `pg_isready`
- Verify DATABASE_URL format: `postgresql://user:pass@host:port/dbname`
- Check credentials: username, password, database name

### Table Already Exists Error
- Drop existing tables: `python -c "from backend.database.db import Base, engine; Base.metadata.drop_all(engine)"`
- Then reinitialize: `python backend/scripts/init_postgres.py`

### Permission Denied Error
- Verify user has privileges:
```sql
GRANT ALL PRIVILEGES ON DATABASE ai_attendance TO attendance_user;
GRANT ALL PRIVILEGES ON SCHEMA public TO attendance_user;
```

### Slow Queries
- Check indexes created: `\d attendance_logs` in psql
- Verify indexes used: `EXPLAIN SELECT ...` in psql
- Check connection pool: `pool_size` and `max_overflow` settings

## Starting the Backend

```bash
cd d:\AI-Attendance-System

# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Start backend
python -m backend.app
```

Expected output:
```
 * Running on http://localhost:5000 (Press CTRL+C to quit)
 * Database: PostgreSQL (ai_attendance)
 * Ready to handle requests
```

## API Testing

### Login (Get JWT Token)
```bash
curl -X POST http://localhost:5000/api/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'
```

### Protected Endpoint (Requires Token)
```bash
curl -X GET http://localhost:5000/api/analytics \
  -H "Authorization: Bearer <token_from_login>"
```

## Production Deployment

### 1. Use RDS or Managed PostgreSQL
- AWS RDS
- Azure Database for PostgreSQL
- Google Cloud SQL
- DigitalOcean Managed Databases

### 2. Connection String
```
DATABASE_URL=postgresql://user:pass@host:5432/ai_attendance
```

### 3. Performance Tuning
```python
# Adjust for production load
engine = create_engine(
    DATABASE_URL,
    pool_size=20,
    max_overflow=40,
    pool_pre_ping=True,
    pool_recycle=3600,  # Recycle connections hourly
)
```

### 4. Backups
```bash
# Automated daily backup
pg_dump -U attendance_user -d ai_attendance > backup_$(date +%Y%m%d).sql
```

## Monitoring

### Check Connection Status
```bash
psql -U attendance_user -d ai_attendance -c "SELECT version();"
```

### View Active Connections
```sql
SELECT * FROM pg_stat_activity;
```

### Check Index Usage
```sql
SELECT schemaname, tablename, indexname, idx_scan
FROM pg_stat_user_indexes
ORDER BY idx_scan DESC;
```

### Monitor Table Size
```sql
SELECT 
    tablename, 
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables 
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

## Support

For issues:
1. Check PostgreSQL logs: `tail -f /var/log/postgresql/postgresql.log`
2. Enable query logging: Set `log_statement = 'all'` in postgresql.conf
3. Review connection pool metrics
4. Check indexes are being used with `EXPLAIN PLAN`

