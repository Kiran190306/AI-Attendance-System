# PostgreSQL Deployment Checklist

## Pre-Deployment

### Environment Setup
- [ ] PostgreSQL installed and running (`pg_isready`)
- [ ] psycopg2 package installed (`pip install psycopg2-binary`)
- [ ] Python 3.9+ available (`python --version`)
- [ ] Virtual environment active

### Database Preparation
- [ ] PostgreSQL admin user created
- [ ] `ai_attendance` database created
- [ ] `attendance_user` user created with password
- [ ] Permissions granted: `GRANT ALL PRIVILEGES ON DATABASE ai_attendance TO attendance_user`

### Configuration
- [ ] `.env` file created in project root
- [ ] `DATABASE_URL` set to correct PostgreSQL connection
- [ ] No hardcoded passwords in code
- [ ] Test connection string locally

## Installation Steps

### Step 1: Install Dependencies
```bash
cd d:\AI-Attendance-System\backend
pip install -r requirements.txt
```
- [ ] Installation completed without errors
- [ ] psycopg2-binary installed
- [ ] sqlalchemy installed

### Step 2: Configure Database
Create `.env` file in project root:
```
DATABASE_URL=postgresql://attendance_user:your_password@localhost:5432/ai_attendance
```
- [ ] `.env` file created
- [ ] DATABASE_URL set correctly
- [ ] Password contains only safe characters

### Step 3: Create PostgreSQL User & Database
```bash
psql -U postgres

# In PostgreSQL console:
CREATE USER attendance_user WITH PASSWORD 'your_secure_password';
CREATE DATABASE ai_attendance OWNER attendance_user;
GRANT ALL PRIVILEGES ON DATABASE ai_attendance TO attendance_user;
\q
```
- [ ] User created
- [ ] Database created
- [ ] Permissions granted
- [ ] Connection verified

### Step 4: Initialize Database Tables
```bash
python backend/scripts/init_postgres.py
```
- [ ] Script runs successfully
- [ ] All tables created
- [ ] Indexes created
- [ ] Admin user created (admin/admin123)
- [ ] Configuration displayed

### Step 5: Verify Installation
```bash
# Test database connection
psql -U attendance_user -d ai_attendance -c "SELECT COUNT(*) FROM users;"

# Should return: 1 (the admin user)
```
- [ ] Database connection works
- [ ] Tables are populated
- [ ] Admin user exists

## Backend Testing

### Step 1: Start Backend Server
```bash
python -m backend.app
```
- [ ] Server starts without errors
- [ ] Port 5000 is available
- [ ] Database connection successful
- [ ] No connection errors in logs

### Step 2: Test Login Endpoint
```bash
curl -X POST http://localhost:5000/api/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'
```
- [ ] Login returns 200 OK
- [ ] Response includes `access_token`
- [ ] Token is JWT format
- [ ] User data in response

### Step 3: Test Protected Endpoint
```bash
# Use token from login response
curl -X GET http://localhost:5000/api/analytics \
  -H "Authorization: Bearer <token_here>"
```
- [ ] Request returns 200 OK
- [ ] Analytics data returned
- [ ] No "Token is missing" error
- [ ] No "Token is invalid" error

### Step 4: Test Invalid Token
```bash
curl -X GET http://localhost:5000/api/analytics \
  -H "Authorization: Bearer invalid_token"
```
- [ ] Returns 401 Unauthorized
- [ ] Error: "Token is invalid"
- [ ] No data leaked

### Step 5: Test Without Token
```bash
curl -X GET http://localhost:5000/api/analytics
```
- [ ] Returns 401 Unauthorized
- [ ] Error: "Token is missing"
- [ ] Protected endpoint verified

## Database Verification

### Verify Tables Created
```bash
psql -U attendance_user -d ai_attendance -c "\dt"
```
- [ ] users table exists
- [ ] students table exists
- [ ] attendance_logs table exists

### Verify Indexes Created
```bash
psql -U attendance_user -d ai_attendance -c "\d attendance_logs"
```
- [ ] idx_attendance_student_name exists
- [ ] idx_attendance_date exists
- [ ] idx_attendance_timestamp exists
- [ ] idx_attendance_student_date exists

### Verify Data
```bash
psql -U attendance_user -d ai_attendance

# Check users
SELECT COUNT(*) FROM users;
# Expected: 1

# Check admin user
SELECT username, email FROM users WHERE username = 'admin';
# Expected: admin, admin@attendance.local

\q
```
- [ ] Admin user exists
- [ ] Email is correct
- [ ] Password hash exists

## API Endpoints Test

### Authentication Endpoints

#### POST /api/login
```bash
curl -X POST http://localhost:5000/api/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'
```
Expected response:
```json
{
  "access_token": "eyJhbGci...",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "username": "admin",
    "email": "admin@attendance.local"
  }
}
```
- [ ] Status 200 OK
- [ ] Token returned
- [ ] User info included

#### POST /api/signup (requires token)
```bash
# First get a token, then:
curl -X POST http://localhost:5000/api/signup \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{"username":"newuser","email":"new@example.com","password":"pass123"}'
```
- [ ] Protected by token
- [ ] Creates new user
- [ ] Returns token for new user

### Protected Endpoints

#### GET /api/analytics
- [ ] Requires token: YES
- [ ] Returns analytics data
- [ ] Status 200 OK

#### GET /api/students
- [ ] Requires token: YES
- [ ] Returns student list
- [ ] Status 200 OK

#### GET /api/attendance
- [ ] Requires token: YES
- [ ] Returns attendance records
- [ ] Status 200 OK

#### GET /api/system/status
- [ ] Requires token: YES
- [ ] Returns dataset stats
- [ ] Status 200 OK

## Performance Verification

### Query Performance
```sql
-- In psql console
EXPLAIN ANALYZE SELECT * FROM attendance_logs WHERE student_name = 'test_student';
EXPLAIN ANALYZE SELECT * FROM attendance_logs WHERE date = CURRENT_DATE;
EXPLAIN ANALYZE SELECT * FROM users WHERE username = 'admin';
```
- [ ] Plans show index use
- [ ] No sequential scans on large tables
- [ ] Query times < 10ms

### Connection Pool Test
```python
# Monitor in separate terminal:
psql -U attendance_user -d ai_attendance -c "SELECT count(*) FROM pg_stat_activity;"
```
- [ ] Pool size normalized around 10
- [ ] No connection leaks
- [ ] Connections reused efficiently

## Security Checklist

### Credentials & Configuration
- [ ] `.env` file created and NOT in git
- [ ] `.gitignore` includes `.env`
- [ ] No passwords in code
- [ ] Admin password changed from default
- [ ] PostgreSQL user password is strong

### Database Security
- [ ] Restricted user privileges (not all superuser)
- [ ] Database user cannot create databases
- [ ] Connection string not logged
- [ ] No SQL injection vulnerabilities

### Network Security
- [ ] PostgreSQL restricted to localhost (development)
- [ ] HTTPS enabled for production
- [ ] API token validation working
- [ ] Unauthorized requests rejected

## Production Deployment

### Before Going Live

#### Database
- [ ] PostgreSQL version documented
- [ ] Backup strategy tested
- [ ] Connection pooling tuned
- [ ] Index statistics updated

#### Backend
- [ ] SECRET_KEY changed from default
- [ ] DEBUG mode disabled
- [ ] CORS_ORIGINS configured
- [ ] Error logging enabled

#### Monitoring
- [ ] Query logging enabled
- [ ] Connection monitoring active
- [ ] Performance baselines recorded
- [ ] Alert thresholds set

#### Documentation
- [ ] DATABASE_URL format documented
- [ ] Backup procedures written
- [ ] Recovery procedures tested
- [ ] Support escalation path clear

### Production Configuration

Update `.env` for production:
```
DATABASE_URL=postgresql://user:password@prod-host:5432/ai_attendance
SECRET_KEY=<new-random-key>
DEBUG=false
CORS_ORIGINS=https://yourdomain.com,https://app.yourdomain.com
ACCESS_TOKEN_EXPIRE_MINUTES=1440
```

- [ ] Production DATABASE_URL set
- [ ] Secret key generated (openssl rand -hex 32)
- [ ] Debug mode disabled
- [ ] CORS properly configured

## Troubleshooting

### Connection Issues
If "could not connect to server":
```bash
# Check PostgreSQL running
pg_isready

# Check connection string
echo $DATABASE_URL

# Test psql connection
psql postgresql://user:pass@host:5432/database
```
- [ ] PostgreSQL service running
- [ ] DATABASE_URL correct
- [ ] Host/port accessible
- [ ] Credentials correct

### Table/Index Issues
If tables don't exist:
```bash
python backend/scripts/init_postgres.py
```
- [ ] Reinitialize database
- [ ] Verify no errors
- [ ] Check tables created

### Query Issues
If queries are slow:
```sql
-- Check index usage
SELECT * FROM pg_stat_user_indexes ORDER BY idx_scan DESC;

-- Update statistics
ANALYZE;
```
- [ ] Indexes created
- [ ] Stats up to date
- [ ] No missing indexes

## Rollback Plan

If issues occur:

1. **Database Rollback**:
```bash
# Stop application
# Restore from backup
psql ai_attendance < backup_2024.sql
# Restart application
```
- [ ] Backup file accessible
- [ ] Restore procedure tested
- [ ] Data integrity verified

2. **Code Rollback**:
```bash
# Revert to previous version with SQLite
git checkout previous_commit
pip install -r backend/requirements.txt
python -m backend.app
```
- [ ] Version history available
- [ ] Previous requirements.txt available
- [ ] Fallback tested

## Sign-Off

- [ ] All steps completed
- [ ] All tests passed
- [ ] Database backed up
- [ ] Documentation reviewed
- [ ] Team notified

**Date Completed**: ___________
**Deployed By**: ___________
**Environment**: [ ] Local [ ] Dev [ ] Staging [ ] Production

## Support

For issues during deployment:
1. Check logs: `tail -f backend.log`
2. Test connection: `psql postgresql://...`
3. Review guide: `POSTGRES_MIGRATION_GUIDE.md`
4. Check status: `POSTGRES_VALIDATION_REPORT.md`

