# PostgreSQL Database Upgrade - Quick Reference

## What Changed

### ✅ Replaced Library
- **Before**: sqlite3 (built-in, file-based)
- **After**: psycopg2 (PostgreSQL adapter)
- **File**: `backend/requirements.txt`

### ✅ Environment Configuration
- **Before**: Hardcoded SQLite path `sqlite:///attendance.db`
- **After**: Database URL from environment variable `DATABASE_URL`
- **File**: `backend/config.py`

### ✅ Connection Options
- **Before**: SQLite with `check_same_thread=False`
- **After**: PostgreSQL with connection pooling (pool_size=10, max_overflow=20)
- **File**: `backend/database/db.py`

### ✅ Database Indexes
- **Before**: Basic indexes on primary lookups
- **After**: Comprehensive indexes for query optimization
- **Files**: `backend/database/models.py`

### ✅ Repository Methods
- **Before**: Simple queries without explicit optimization
- **After**: Optimized with `and_()` conditions and proper ordering
- **File**: `backend/database/repository.py`

### ✅ New Methods Added
- `list_by_date_range()` - Date range queries
- `get_by_student_and_date()` - Composite lookup queries
- **File**: `backend/database/repository.py`

## 1-Minute Setup

### Step 1: Install Dependencies
```bash
cd backend
pip install -r requirements.txt
```

### Step 2: Create PostgreSQL Database
```bash
# Windows: Use pgAdmin or psql
psql -U postgres
CREATE USER attendance_user WITH PASSWORD 'secure_password_here';
CREATE DATABASE ai_attendance OWNER attendance_user;
\q
```

### Step 3: Set Environment Variable
Create `.env` file:
```
DATABASE_URL=postgresql://attendance_user:secure_password_here@localhost:5432/ai_attendance
```

### Step 4: Initialize Database
```bash
python backend/scripts/init_postgres.py
```

### Step 5: Start Backend
```bash
python -m backend.app
```

## Table Definitions

### users
```
- id (SERIAL PRIMARY KEY)
- username (VARCHAR 255, UNIQUE, INDEXED)
- email (VARCHAR 255, UNIQUE, INDEXED)
- hashed_password (VARCHAR 255)
- created_at (TIMESTAMP, INDEXED)
```

### students
```
- id (SERIAL PRIMARY KEY)
- name (VARCHAR 255, UNIQUE, INDEXED)
- created_at (TIMESTAMP, INDEXED)
```

### attendance_logs
```
- id (SERIAL PRIMARY KEY)
- student_name (VARCHAR 255, INDEXED)
- date (DATE, INDEXED)
- timestamp (TIMESTAMP, INDEXED DESC)
- confidence (FLOAT)
- UNIQUE(student_name, date)
- COMPOSITE INDEX(student_name, date)
```

## Performance

### Indexes Implemented
- **users**: 3 indexes (username, email, created_at)
- **students**: 2 indexes (name, created_at)
- **attendance_logs**: 4 indexes + 1 composite (student_name, date, timestamp DESC, [student_name, date])

### Query Optimization
```python
# ✓ Fast: O(log N) lookup
db.query(AttendanceLog).filter(
    and_(
        AttendanceLog.student_name == name,
        AttendanceLog.date == today
    )
).first()

# ✓ Fast: O(log N) lookup
db.query(StudentRepository).filter(
    Student.name == "John"
).first()

# ✓ Fast: O(log N) range scan
db.query(AttendanceLog).filter(
    AttendanceLog.date >= start_date
).all()
```

### Connection Pooling
- **Pool Size**: 10 (connections to keep ready)
- **Max Overflow**: 20 (additional connections on demand)
- **Pool Pre-Ping**: Enabled (checks connection health)

## Environment Variables

### Required
```
DATABASE_URL=postgresql://user:password@host:port/database
```

### Example
```
DATABASE_URL=postgresql://attendance_user:secure_password_here@localhost:5432/ai_attendance
```

### Format
```
postgresql://[username]:[password]@[host]:[port]/[database]
```

## Default Admin Credentials

Created by `init_postgres.py`:
- **Username**: admin
- **Password**: admin123
- **⚠ Change immediately in production!**

## Files Modified

1. **backend/requirements.txt**
   - Removed: `aiomysql>=0.2.0`
   - Removed: `sqlalchemy[asyncio]>=2.0.25`
   - Added: `psycopg2-binary>=2.9.9`
   - Changed: `sqlalchemy>=2.0.25` (non-async)

2. **backend/config.py**
   - Added environment variable support
   - Changed to PostgreSQL connection string

3. **backend/database/db.py**
   - Removed SQLite-specific settings
   - Added PostgreSQL connection pooling
   - Added connection event listeners

4. **backend/database/models.py**
   - Added comprehensive Index definitions
   - Indexed created_at for all tables
   - Added composite index on (student_name, date)

5. **backend/database/repository.py**
   - Updated queries to use explicit `and_()` conditions
   - Added optimization comments
   - Added new methods: `list_by_date_range()`, `get_by_student_and_date()`

6. **.env.example**
   - Updated database format to PostgreSQL
   - Removed MySQL-specific variables

## New Files

1. **backend/scripts/init_postgres.py**
   - Initialization script
   - Creates tables with indexes
   - Sets up admin user
   - Verifies connection

2. **POSTGRES_MIGRATION_GUIDE.md**
   - Comprehensive migration guide
   - PostgreSQL installation instructions
   - Performance tuning details
   - Troubleshooting section

## Verification Checklist

- [ ] PostgreSQL installed and running
- [ ] Database created: `ai_attendance`
- [ ] Database user created: `attendance_user`
- [ ] `.env` file created with `DATABASE_URL`
- [ ] Dependencies installed: `pip install -r backend/requirements.txt`
- [ ] Database initialized: `python backend/scripts/init_postgres.py`
- [ ] Backend starts: `python -m backend.app`
- [ ] Login works: `POST /api/login`
- [ ] Protected endpoint works: `GET /api/analytics`

## Troubleshooting

### "Could not connect to server"
Check PostgreSQL is running:
```bash
pg_isready
# Expected: accepting connections
```

### "FATAL: Ident authentication failed"
Update pg_hba.conf to use md5/scram-sha-256 authentication

### "Does not exist" on table queries
Run initialization:
```bash
python backend/scripts/init_postgres.py
```

### Slow queries
Check indexes are created:
```sql
-- In PostgreSQL
\d attendance_logs
```

## Migration from SQLite

If migrating existing data:
```bash
# Export from SQLite
sqlite3 attendance.db ".dump" > backup.sql

# Import structure to PostgreSQL
psql -U attendance_user -d ai_attendance < backup.sql

# Verify data
psql -U attendance_user -d ai_attendance -c "SELECT COUNT(*) FROM attendance_logs;"
```

## Production Deployment

### Environment Variable for Render/Heroku
```
DATABASE_URL=postgresql://user:password@prod-host:5432/ai_attendance
```

### Environment Variable for AWS RDS
```
DATABASE_URL=postgresql://admin:password@ai-attendance-prod.c5z4k2f9d4j5.us-east-1.rds.amazonaws.com:5432/ai_attendance
```

### Connection Pooling for Production
Update `backend/database/db.py`:
```python
engine = create_engine(
    DATABASE_URL,
    pool_size=20,           # More connections for production
    max_overflow=40,        # Allow more overflow
    pool_pre_ping=True,     # Verify connections
    pool_recycle=3600,      # Recycle hourly (RDS requirement)
)
```

## Performance Benchmarks

Expected query times (estimated on standard server):
- Single user lookup by username: ~1ms (indexed)
- All students list: ~10ms (indexed scan, typical 100-1000 students)
- Today's attendance: ~5ms (indexed on date)
- 7-day attendance report: ~50ms (date range scan)
- Connection setup: <100ms (pooled)

## Support Documentation

- Full guide: `POSTGRES_MIGRATION_GUIDE.md`
- Repository queries: `backend/database/repository.py`
- Model definitions: `backend/database/models.py`
- Configuration: `backend/config.py`

