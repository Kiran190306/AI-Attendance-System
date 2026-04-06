"""
INTEGRATION GUIDE - Face Recognition with Existing Attendance System
======================================================================

This guide explains how to integrate the new face recognition system
with your existing attendence system components.
"""

# ============================================================================
# 1. DATABASE INTEGRATION
# ============================================================================

"""
New fields in Student model:
  - face_embedding (bytes): 512 bytes for 128-d float32 embedding
  - embeddings_count (int): Number of source images used
  - embeddings_updated_at (datetime): Last update timestamp

To migrate existing database:

UPDATE students SET face_embedding = NULL, embeddings_count = 0;
ALTER TABLE students ADD COLUMN embeddings_updated_at DATETIME;

Or if using SQLAlchemy:
  python scripts/init_db.py  # Creates tables automatically
"""

# ============================================================================
# 2. BACKEND INTEGRATION
# ============================================================================

"""
A. Face Engine Integration with API

  File: backend/app/core/face_engine.py
  
  New functions:
  - extract_embedding_from_array(image: np.ndarray) -> np.ndarray
  - extract_embedding_from_base64(data: str) -> np.ndarray
  - compute_embedding_distance(e1, e2) -> float
  - recognize_face_from_embedding(embedding, students_db) -> (name, confidence)
  - batch_recognize_faces_from_embeddings(embeddings, students_db) -> list

B. API Endpoints (backend/app/api/v1/face.py)

  POST /api/v1/face/recognize
    - Test face recognition without marking
    - Returns: {recognized: bool, student_id, confidence, ...}
    - Use for: Debugging, testing, demo

  POST /api/v1/face/mark
    - Mark attendance with face recognition
    - Requires: session_id, image_data (base64)
    - Returns: Attendance record with metadata
    - Use for: Production attendance marking

  GET /api/v1/face/status
    - Get engine capabilities and stats
    - Returns: {EMBEDDING_THRESHOLD, CONFIDENCE_THRESHOLD, ...}
    - Use for: Client-side configuration

  POST /api/v1/face/update-embedding
    - Update individual student embedding
    - Use for: Manual enrollment or re-enrollment

C. Error Handling

  Handled exceptions:
  - No face detected: "No single face detected"
  - Low confidence: "Confidence too low ({confidence:.1%})"
  - Unknown face: "Face not recognized"
  - Database error: Standard AppException

D. Authentication

  All endpoints protected by:
  - @Depends(RequireTeacher) for authentication
  - JWT token validation
  - Role-based access control

E. CORS Configuration

  Add to settings:
    FACE_API_CORS_ORIGINS = ["http://localhost:3000", ...]
"""

# ============================================================================
# 3. FRONTEND INTEGRATION
# ============================================================================

"""
A. Camera Component

  File: frontend/src/components/Camera.tsx (example)
  
  Steps:
  1. Request camera access (getUserMedia)
  2. Capture frame as canvas
  3. Convert to base64
  4. Send to /api/v1/face/recognize or /api/v1/face/mark
  5. Display result

  Example:
  
  const captureAndRecognize = async () => {
    const canvas = videoRef.current.captureToCanvas();
    const imageData = canvas.toDataURL('image/jpeg');
    
    const response = await api.post('/face/recognize', {
      image_data: imageData
    });
    
    setResult(response.data);
  };

B. Confidence Display

  Show confidence score:
  - Green if confidence >= 0.65
  - Yellow if 0.5 <= confidence < 0.65
  - Red if confidence < 0.5

C. Error Handling

  Catch and display:
  - "No face detected" -> "Please position your face in frame"
  - "Confidence too low" -> "Please try again with better lighting"
  - Network errors -> "Connection error. Please retry"

D. Live Feedback

  Show real-time info:
  - "Face detected: X.X%"
  - "Processing..."
  - "Recognized: John Doe (92%)"
  - "Unknown face"
"""

# ============================================================================
# 4. DATASET PREPARATION WORKFLOW
# ============================================================================

"""
Step 1: Use camera capture utility

  python scripts/capture_training_images.py "John Doe" --num 10
  
  This creates: dataset/John Doe/face_001.jpg ... face_010.jpg

Step 2: Validate dataset structure

  dataset/
  ├── John Doe/
  │   ├── face_001.jpg
  │   ├── face_002.jpg
  │   └── ... (5-10 images)
  ├── Jane Smith/
  │   ├── face_001.jpg
  │   └── ... (5-10 images)
  └── ...

Step 3: Generate embeddings

  cd backend
  python scripts/generate_embeddings.py --dataset ../dataset --verify
  
  Output:
  - Embeddings stored in Student.face_embedding column
  - Ready for real-time use

Step 4: Test recognition

  python ../face_test.py
  
  Should show:
  - Green boxes for recognized students
  - Confidence scores
  - Performance metrics
"""

# ============================================================================
# 5. REAL-TIME SYSTEM INTEGRATION
# ============================================================================

"""
Option A: Standalone Real-Time System

  python attendance_system.py
  
  Features:
  - Live camera feed
  - Real-time recognition
  - Automatic attendance marking
  - CSV output

Option B: Backend API-based

  POST /api/v1/face/mark
  {
    "session_id": 1,
    "image_data": "data:image/jpeg;base64,..."
  }
  
  Workflow:
  1. Frontend captures image from camera
  2. Sends to API endpoint
  3. Backend extracts embedding
  4. Matches against database
  5. Marks attendance
  6. Returns confirmation

Option C: Hybrid

  - Real-time system captures and marks locally
  - Syncs to database periodically
  - Uses websocket for live updates to frontend
"""

# ============================================================================
# 6. CONFIGURATION INTEGRATION
# ============================================================================

"""
Environment Variables (backend/.env)

  # Recognition thresholds
  EMBEDDING_DISTANCE_THRESHOLD=0.60
  FACE_RECOGNITION_CONFIDENCE=0.65
  
  # Database
  DATABASE_URL=mysql+aiomysql://user:pass@localhost/ai_attendance
  
  # API
  CORS_ORIGINS=["http://localhost:3000"]
  SECRET_KEY=your-secret-key-here

Python Configuration (backend/app/config.py)

  class Settings:
      EMBEDDING_MATCH_THRESHOLD: float = 0.60
      FACE_RECOGNITION_CONFIDENCE: float = 0.65
      FACE_DETECTION_MODEL: str = "hog"  # or "cnn"
      ...

Command-line Configuration (attendance_system.py)

  python attendance_system.py \
    --threshold 0.60 \
    --confidence 0.65 \
    --frame-skip 2 \
    --detection-scale 0.5
"""

# ============================================================================
# 7. MONITORING & LOGGING
# ============================================================================

"""
Backend Logging

  import logging
  logger = logging.getLogger(__name__)
  
  Logs include:
  - Face recognition: "Recognized: John Doe (distance=0.35, confidence=92%)"
  - No match: "Face not recognized (min_distance=1.05 > 0.60)"
  - Errors: "Error extracting embedding: ..."

Performance Metrics

  stats = recognizer.get_recognition_stats()
  # Returns:
  {
    "total_recognitions": 1234,
    "successful_recognitions": 1200,
    "success_rate": "97.2%",
    "avg_recognition_time_ms": 45.2,
    "enrolled_students": 25,
  }

Database Auditing

  attendance_log.csv format:
  name, timestamp, confidence, marked_by_face
  John Doe, 2025-02-15 10:30:45, 0.92, true

Real-time Dashboard

  Show live metrics:
  - Active recognitions
  - Recognition accuracy
  - System performance
  - Unrecognized faces
"""

# ============================================================================
# 8. ROLLOUT STRATEGY
# ============================================================================

"""
Phase 1: Pilot (1-2 weeks)
  - Capture dataset for small group (10-20 students)
  - Generate embeddings
  - Test recognition accuracy
  - Gather feedback
  - Tune thresholds

Phase 2: Expand (1-2 weeks)
  - Add more students (~50)
  - Test in real sessions
  - Monitor false positives
  - Optimize performance

Phase 3: Production (ongoing)
  - Deploy to live system
  - Monitor accuracy metrics
  - Handle edge cases
  - Update dataset as needed

Fallback Plans

  - Always keep manual attendance marking available
  - If face recognition fails: use manual backup
  - If database error: use local CSV logging
  - Gradual rollout reduces risk
"""

# ============================================================================
# 9. TESTING CHECKLIST
# ============================================================================

"""
Integration Tests

  [ ] Face detection works with real camera
  [ ] Embeddings generated successfully
  [ ] Stored embeddings retrieved from database
  [ ] Recognition accuracy >= 95% on test set
  [ ] Confidence scores are between 0-1
  [ ] Unknown faces properly rejected
  [ ] API endpoint authentication working
  [ ] Error handling for missing face
  [ ] Error handling for low confidence
  [ ] Database transactions committed properly
  [ ] Performance meets requirements (50-100ms)

Edge Cases

  [ ] Multiple faces in frame
  [ ] Face partially occluded
  [ ] Poor lighting conditions
  [ ] Similar-looking faces
  [ ] Face dimensions too small/too large
  [ ] Camera quality variations
  [ ] Network latency issues
  [ ] Database connection failures

Performance Tests

  [ ] 50 students: < 100ms per recognition
  [ ] 100 students: < 150ms per recognition
  [ ] Real-time: 10+ FPS sustained
  [ ] Memory: < 500MB resident
  [ ] CPU: < 50% single core
"""

# ============================================================================
# 10. TROUBLESHOOTING DURING INTEGRATION
# ============================================================================

"""
Issue: "Module not found: face_recognition"
Fix:   pip install face-recognition

Issue: "Face not recognized despite valid dataset"
Fix:   1. Verify dataset structure
       2. Check embeddings generated: python backend/scripts/generate_embeddings.py --verify
       3. Check confidence/distance thresholds
       4. Capture better quality images (lighting, angle, distance)

Issue: "Too many false positives"
Fix:   1. Lower confidence threshold: MIN_RECOGNITION_CONFIDENCE = 0.70
       2. Lower distance threshold: EMBEDDING_DISTANCE_THRESHOLD = 0.55
       3. Generate more diverse dataset

Issue: "System too slow (> 200ms per recognition)"
Fix:   1. Increase FRAME_SKIP
       2. Decrease DETECTION_SCALE
       3. Reduce CAMERA_WIDTH/HEIGHT resolution
       4. Use GPU acceleration if available

Issue: "Database errors when storing embeddings"
Fix:   1. Check database connection
       2. Verify schema has face_embedding column
       3. Check file permissions
       4. Check disk space

Issue: "API returns 401 Unauthorized"
Fix:   1. Verify JWT token in request
       2. Check token expiration
       3. Verify CORS settings
       4. Check user role (must be Teacher)
"""

# ============================================================================
# 11. MAINTENANCE SCHEDULE
# ============================================================================

"""
Daily

  - Monitor recognition accuracy logs
  - Check for failed recognitions
  - Monitor system performance metrics

Weekly

  - Backup attendance database
  - Review unrecognized faces
  - Check API error logs
  - Verify performance benchmarks

Monthly

  - Regenerate embeddings if dataset changed
  - Review and adjust confidence thresholds
  - Analyze attendance patterns
  - Update system documentation

Quarterly

  - Audit database integrity
  - Review and update security settings
  - Performance optimization
  - User feedback collection

Annually

  - Full system audit
  - Upgrade dependencies
  - Recapture dataset with recent photos
  - Update documentation
  - Plan improvements
"""

# ============================================================================
# SUMMARY
# ============================================================================

"""
The face recognition upgrade integrates with your system through:

1. Database Layer
   - New fields in Student model
   - Embeddings persisted in database

2. API Layer
   - New face recognition endpoints
   - Confidence scoring and validation
   - Integration with existing auth/roles

3. Business Logic
   - Real-time attendance marking
   - Unknown face handling
   - Dataset management

4. Frontend
   - Camera access and capture
   - Real-time recognition display
   - Confidence visualization

5. Operations
   - Dataset preparation workflows
   - Monitoring and logging
   - Performance optimization
   - Maintenance schedules

For detailed documentation, see:
- FACE_RECOGNITION_UPGRADE.md
- QUICKSTART.md
- source code docstrings
"""
