# Logging System Documentation

## Overview

Comprehensive logging system for the AI Attendance System with:
- ✅ API call logging (all requests/responses)
- ✅ Error logging with stack traces
- ✅ Rotating file handler (10MB max, 10 backups)
- ✅ Console output for development
- ✅ Structured logging format
- ✅ Module-specific loggers

## Log Files

### logs/app.log
Main application log file containing:
- All API requests and responses
- Error messages with stack traces
- Authentication events
- Attendance processing events
- System startup/shutdown

### Location
```
d:\AI-Attendance-System\
└── logs/
    └── app.log          # Current log file
    └── app.log.1        # Previous log (rotated)
    └── app.log.2-10     # Archive logs
```

## Log Format

```
2024-04-10 14:35:22,123 - INFO - backend.app - Application starting up...
2024-04-10 14:35:23,456 - INFO - backend.app - Database initialized successfully
2024-04-10 14:35:24,789 - INFO - backend.api.routes_auth - Successful login for user: admin
2024-04-10 14:35:25,012 - ERROR - backend.api.routes_auth - Error generating token for user admin: ...
```

Format: `%(asctime)s - %(levelname)s - %(name)s - %(message)s`

## Log Levels

| Level | Usage | Example |
|-------|-------|---------|
| DEBUG | Detailed information | Function entry, detailed flow |
| INFO | General information | Successful operations, important events |
| WARNING | Warning messages | Failed login attempt, missing data |
| ERROR | Error messages | Exception occurred, operation failed |
| CRITICAL | Critical errors | System shutdown |

## Configuration

### backend/config.py
```python
LOG_FORMAT: str = "%(asctime)s - %(levelname)s - %(name)s - %(message)s"
LOG_LEVEL: str = "INFO"  # Can be DEBUG, INFO, WARNING, ERROR, CRITICAL
```

### backend/utils/logger.py
```python
# File handler settings
maxBytes=10 * 1024 * 1024  # 10MB per file
backupCount=10             # Keep 10 rotated backups
```

## Getting Loggers

### In your module:
```python
import logging

# Get module-specific logger
logger = logging.getLogger(__name__)

# Use logger
logger.info("Event happened")
logger.error("Error occurred", exc_info=True)
```

### Root logger:
```python
from backend.utils.logger import get_logger

logger = get_logger("my_module")
```

## Logged Events

### Authentication (routes_auth.py)
- ✅ Login attempts (with username)
- ✅ Failed login attempts (with IP)
- ✅ Successful login
- ✅ User registration
- ✅ Token generation errors

### API Requests (middleware)
- ✅ Incoming request (method, path, IP, user agent)
- ✅ Response status code
- ✅ Request duration
- ✅ Unhandled exceptions

### Attendance (routes_attendance.py)
- ✅ Attendance record retrieval
- ✅ Date filtering results
- ✅ CSV download attempts
- ✅ Query errors

### Analytics (routes_analytics.py)
- ✅ Analytics report generation
- ✅ Summary statistics
- ✅ Generation errors

### Students (routes_students.py)
- ✅ Student list retrieval
- ✅ New student addition
- ✅ Missing field errors

### System (routes_system.py)
- ✅ System status checks
- ✅ Dataset statistics

### Mobile API (routes_mobile.py)
- ✅ Face recognition engine initialization
- ✅ Mobile attendance submissions
- ✅ Face detection results (no face, unrecognized, recognized)
- ✅ Attendance marking (new or duplicate)
- ✅ Invalid image handling
- ✅ Device information

### Database (db.py)
- ✅ Database initialization
- ✅ Connection status

### Application (app.py)
- ✅ Startup process
- ✅ Blueprint registration
- ✅ Database initialization status
- ✅ Error handling

## Reading Logs

### View recent logs:
```bash
# Last 50 lines
tail -50 logs/app.log

# Real-time (follow)
tail -f logs/app.log

# Search for errors
grep ERROR logs/app.log

# Search for specific user
grep "admin" logs/app.log

# Count by level
grep -c "ERROR" logs/app.log
grep -c "WARNING" logs/app.log
```

### View all logs:
```bash
# Recent events
cat logs/app.log | tail -100

# Specific date
grep "2024-04-10" logs/app.log

# Specific endpoint
grep "/api/login" logs/app.log
```

## Log Rotation

### Automatic Rotation
- Triggered when log file reaches 10MB
- Keeps last 10 backups automatically
- Old backups are overwritten

### Example:
```
logs/app.log       # Current (< 10MB)
logs/app.log.1     # Rotated at 10MB
logs/app.log.2     # Previous rotation
...
logs/app.log.10    # Oldest backup
```

### Manual Rotation:
```python
import logging.handlers
handler = logging.getLogger().handlers[0]
if isinstance(handler, logging.handlers.RotatingFileHandler):
    handler.doRollover()
```

## Environment Variables

### Change log level:
```bash
export LOG_LEVEL=DEBUG
python -m backend.app
```

### Supported levels:
- `DEBUG` - Most verbose
- `INFO` - Normal operations
- `WARNING` - Potential issues
- `ERROR` - Error conditions
- `CRITICAL` - System critical

## Error Logging

### With stack trace:
```python
try:
    something_risky()
except Exception as e:
    logger.error("Operation failed", exc_info=True)
    # Stack trace automatically included
```

### Without stack trace:
```python
logger.error("User not found: admin")
# Simple error message
```

## Key Files Modified

1. **backend/utils/logger.py**
   - Enhanced logging setup
   - File handler with rotation
   - Console handler for development

2. **backend/utils/request_logger.py** (NEW)
   - Request/response middleware
   - Timing information
   - Error handler

3. **backend/app.py**
   - Request logging middleware registration
   - Database initialization logging
   - Error handling with logging

4. **backend/api/routes_auth.py**
   - Login/signup logging
   - Failed attempt tracking
   - User activity logging

5. **backend/api/routes_attendance.py**
   - Attendance query logging
   - Date filter results

6. **backend/api/routes_analytics.py**
   - Analytics calculation logging

7. **backend/api/routes_students.py**
   - Student operations logging

8. **backend/api/routes_system.py**
   - System status logging

9. **backend/api/routes_mobile.py**
   - Face recognition logging
   - Mobile attendance events

## Performance Impact

- **Minimal**: Async logging where possible
- **File I/O**: Buffered and efficient
- **Memory**: Rotating logs prevent disk overflow
- **Network**: No remote logging (local file only)

## Security Considerations

- ✅ No passwords logged
- ✅ Sensitive data not logged
- ✅ File permissions: 644 (readable)
- ✅ Log files in git-ignored `logs/` directory
- ✅ Can be archived and deleted safely

## Monitoring & Alerts

### Check for errors:
```bash
# Find all errors
grep ERROR logs/app.log | wc -l

# Recent errors
grep ERROR logs/app.log | tail -20

# Errors by module
grep ERROR logs/app.log | cut -d' ' -f5 | sort | uniq -c
```

### Check API response times:
```bash
# Extract response times
grep "Response:" logs/app.log | grep -o "[0-9]*\.[0-9]*s"

# Slow requests (> 1s)
grep "Response:" logs/app.log | awk '$NF ~ /[1-9][0-9]*\.[0-9]*s/ {print}'
```

### Check failed logins:
```bash
grep "Failed login" logs/app.log
```

## Debugging Tips

### Enable DEBUG logging:
Create `.env`:
```
LOG_LEVEL=DEBUG
```

### Trace a specific request:
```bash
# Find request in log
grep "GET /api/attendance" logs/app.log

# Find matching response
grep "Response.*GET /api/attendance" logs/app.log
```

### Monitor live:
```bash
tail -f logs/app.log | grep -E "(ERROR|WARNING|INFO)"
```

## Troubleshooting

### Logs not created:
- Check `logs/` directory exists
- Verify write permissions: `chmod 755 logs/`
- Restart backend application

### Logs not rotating:
- Check file size: `ls -lh logs/app.log`
- Verify rotation settings in logger.py
- Check disk space: `df -h`

### Performance degradation:
- Check disk I/O: `iostat`
- Maybe disable DEBUG logging
- Archive old logs: `gzip logs/app.log.* && rm logs/app.log.[2-9]*`

## Next Steps

1. Monitor logs for errors
2. Set up log aggregation for production
3. Create alerting rules for ERROR/CRITICAL entries
4. Archive logs periodically (weekly/monthly)
5. Implement centralized logging if needed

