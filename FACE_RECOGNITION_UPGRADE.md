"""
FACE RECOGNITION SYSTEM UPGRADE GUIDE
=====================================

This document explains the production-ready face recognition upgrade with real embeddings.

## Architecture Overview

### Key Components

1. **Embeddings Generator** (embeddings_generator.py)
   - Extracts 128-d face embeddings from dataset images
   - Averages multiple embeddings per student for robust matching
   - Quality control: rejects images with 0 or >1 faces

2. **Student Model Enhanced**
   - Stores averaged 128-d face embedding (face_embedding field)
   - Tracks embeddings count and update timestamp
   - has_valid_embedding() method for validation

3. **Backend Face Engine** (core/face_engine.py)
   - Extract embeddings from base64 images
   - Compute Euclidean distance between embeddings
   - Confidence scoring (0-1 scale)
   - Batch processing support

4. **API Endpoints** (api/v1/face.py)
   - /face/recognize: Test face recognition without marking
   - /face/mark: Mark attendance with face recognition
   - /face/update-embedding: Update student embedding
   - /face/status: Get engine capabilities

5. **Real-Time Recognizer** (attendance_system.py)
   - Live camera feed with real-time face detection
   - Embeddings-based recognition
   - Automatic attendance marking
   - Performance optimizations (frame skipping, scaling)

6. **Optimized Recognizer** (optimized_recognizer.py)
   - Production-grade with caching
   - Performance metrics tracking
   - Batch processing
   - Displacement disk cache

## Installation & Setup

### Step 1: Install Dependencies

```bash
# Backend dependencies (already in requirements.txt)
pip install face-recognition
pip install mediapipe
pip install opencv-contrib-python

# Ensure numpy and pillow are installed
pip install numpy pillow
```

### Step 2: Prepare Dataset

Create a dataset directory with face images organized by student:

```
dataset/
  ├── Student Name 1/
  │   ├── face_001.jpg
  │   ├── face_002.jpg
  │   └── face_003.jpg
  ├── Student Name 2/
  │   ├── face_001.jpg
  │   └── face_002.jpg
  └── ...
```

**Important**: 
- Each subdirectory name should match the student's full name in the database
- Images should be named `face_*.jpg` (jpg, jpeg, or png)
- Each image should contain exactly ONE clear face
- Recommended: 5-10 images per student for best results
- Images should be taken in different angles, lighting, and distances

### Step 3: Generate Embeddings (Backend DB)

Run the embeddings generation script:

```bash
cd backend
python scripts/generate_embeddings.py --dataset ../dataset --verify
```

**Options:**
- `--dataset`: Path to dataset directory (default: dataset/)
- `--verify`: Verify embeddings after generation
- `--db-url`: Custom database URL if not using default

**Output example:**
```
2025-02-15 10:30:45 - INFO - Processing Student Name 1: 8 images
2025-02-15 10:30:48 - INFO - Generated 8 embeddings for Student Name 1
2025-02-15 10:30:50 - INFO - Updated embeddings for Student Name 1 (8 source images)
...
2025-02-15 10:31:05 - INFO - Verified 25 students with embeddings
```

### Step 4: Run Real-Time Attendance

Option A: Use backend API
```bash
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Then use the frontend or API client to mark attendance via `/face/mark`.

Option B: Use standalone system
```bash
python attendance_system.py
```

This runs real-time face recognition on your default camera.

## Configuration

### Confidence Thresholds

In **backend/app/api/v1/face.py**:
```python
MIN_RECOGNITION_CONFIDENCE = 0.65  # 65% minimum
EMBEDDING_DISTANCE_THRESHOLD = 0.60  # Strict matching
```

Lower values = stricter matching (fewer false positives, fewer matches)
Higher values = more lenient (more matches, more false positives)

### In attendance_system.py:
```python
EMBEDDING_DISTANCE_THRESHOLD = 0.60
MIN_RECOGNITION_CONFIDENCE = 0.65
FRAME_SKIP = 2  # Process every 2nd frame
DETECTION_SCALE = 0.5  # Scale for faster detection
```

### Database Field

In **Student model**:
- `face_embedding`: 128-d vector (512 bytes when stored as float32)
- `embeddings_count`: Number of source images used
- `embeddings_updated_at`: Timestamp of last update

## How It Works

### Matching Algorithm

1. **Live Face Detection**: MediaPipe detects faces in camera frame
2. **Embedding Extraction**: face_recognition lib extracts 128-d vector
3. **Distance Computation**: Euclidean distance to all stored embeddings
4. **Confidence Scoring**: 1.0 - (distance / threshold)
5. **Matching**: If confidence >= MIN_RECOGNITION_CONFIDENCE, match found
6. **Attendance**: Mark attendance only on high-confidence match

### Key Benefits

✓ **High Accuracy**: ResNet-based 128-d embeddings (industry standard)
✓ **Real-Time**: ~50-100ms per face recognition
✓ **Low False Positives**: Confidence thresholds prevent wrong matches
✓ **Unknown Face Handling**: Clearly labels unrecognized faces
✓ **Production Ready**: Database persistence, error handling, logging
✓ **Optimized**: Frame skipping, scaling, caching for performance

## Preventing False Positives

### 1. Use High Confidence Threshold
```python
MIN_RECOGNITION_CONFIDENCE = 0.70  # Stricter
EMBEDDING_DISTANCE_THRESHOLD = 0.55  # Stricter
```

### 2. Generate High-Quality Dataset
- Natural lighting (avoid harsh shadows)
- Clear face visibility (face fills 50% of image)
- Varied angles (front, 30°, 45°, side)
- Multiple samples per student (5-10 images)
- Fresh dataset (regenerate embeddings when dataset changes)

### 3. Monitor Confidence Scores
The API returns confidence scores. Log and analyze:
- Patterns of low-confidence matches
- False positives
- Missed recognitions

### 4. Regenerate Embeddings
If accuracy drops:
```bash
python backend/scripts/generate_embeddings.py --dataset ../dataset
```

## Testing

### API Testing

1. Test recognition:
```bash
curl -X POST http://localhost:8000/api/v1/face/recognize \
  -H "Content-Type: application/json" \
  -d '{"image_data": "data:image/jpeg;base64,..."}'
```

2. Test engine status:
```bash
curl http://localhost:8000/api/v1/face/status
```

### Real-Time Testing

```bash
python attendance_system.py
# Press 'Q' to quit
# Check attendance.csv for marked students
```

## Performance Optimization

### Real-Time System (attendance_system.py)

1. **Frame Skipping**: FRAME_SKIP = 2
   - Process only every Nth frame
   - 30 FPS camera → 15 FPS processing

2. **Detection Scaling**: DETECTION_SCALE = 0.5
   - Run detection on 50% resolution
   - Faster detection, same accuracy

3. **Camera Resolution**: 
   ```python
   cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
   cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
   ```

4. **Vectorized Operations**: All embeddings compared at once

### Expected Performance

- Face detection: ~30-50ms per frame
- Embedding extraction: ~20-40ms per face
- Matching: ~5-10ms per face
- Total per frame: ~50-100ms (10-20 FPS)

## Monitoring & Logging

### Logs Location

- Backend: `logs/` directory
- Real-time: stdout with timestamps

### Key Metrics

```python
recognizer.get_recognition_stats()
# Returns:
{
    "total_recognitions": 1234,
    "successful_recognitions": 1200,
    "success_rate": "97.2%",
    "avg_recognition_time_ms": 45.2,
    "enrolled_students": 25,
}
```

## Troubleshooting

### Issue: "No face detected"
**Solution:**
- Ensure good lighting
- Face should be clearly visible
- Try from different angle

### Issue: "Face not recognized"
**Solution:**
- Check dataset directory structure
- Verify embeddings are generated: `python backend/scripts/generate_embeddings.py --verify`
- Check confidence thresholds
- Regenerate embeddings with better images

### Issue: Multiple false recognitions
**Solution:**
- Lower confidence threshold:
  ```python
  MIN_RECOGNITION_CONFIDENCE = 0.70
  EMBEDDING_DISTANCE_THRESHOLD = 0.55
  ```
- Generate more diverse dataset images
- Add more students' images to dataset

### Issue: Camera not opening
**Solution:**
```bash
# Check available cameras
python -c "import cv2; print(cv2.VideoCapture(0).isOpened())"

# Try different camera index
python attendance_system.py  # Edit FRAME_SKIP or camera to test
```

## Database Schema

### Student Model

```python
class Student(Base):
    id: int (PK)
    student_id: str (unique)
    full_name: str
    email: str
    face_embedding: bytes (512 bytes for 128-d float32)
    embeddings_count: int
    embeddings_updated_at: datetime
    is_active: bool
    created_at: datetime
    updated_at: datetime
```

### Migration (if upgrading existing DB)

```bash
# Sync new fields
cd backend
python -c "from app.database import Base, engine; Base.metadata.create_all(engine)"
```

## Best Practices

1. **Regular Dataset Maintenance**
   - Remove invalid images (multiple faces, no face)
   - Re-capture if lighting changes
   - Add new students promptly

2. **Embedding Regeneration**
   - After adding new students
   - After dataset updates
   - If accuracy degrades

3. **Confidence Monitoring**
   - Log all recognitions with confidence
   - Detect patterns of low-confidence matches
   - Adjust thresholds based on data

4. **System Tuning**
   - Test with your specific lighting conditions
   - Tune FRAME_SKIP and DETECTION_SCALE
   - Profile performance on your hardware

5. **Error Handling**
   - Always handle "Unknown" faces gracefully
   - Log unrecognized faces for audit
   - Provide manual fallback attendance marking

## API Reference

### POST /api/v1/face/recognize

Recognize face without marking attendance.

**Request:**
```json
{
  "image_data": "data:image/jpeg;base64,..."
}
```

**Response (matched):**
```json
{
  "recognized": true,
  "student_id": 1,
  "student_name": "John Doe",
  "confidence": 0.92,
  "distance": 0.35,
  "message": "Recognized: John Doe (92% confidence)"
}
```

**Response (not matched):**
```json
{
  "recognized": false,
  "student_id": null,
  "student_name": null,
  "confidence": 0.0,
  "distance": 1.05,
  "message": "Face not recognized"
}
```

### POST /api/v1/face/mark

Mark attendance via face recognition.

**Request:**
```json
{
  "session_id": 1,
  "image_data": "data:image/jpeg;base64,..."
}
```

**Response:**
```json
{
  "id": 42,
  "session_id": 1,
  "student_id": 1,
  "student_name": "John Doe",
  "status": "present",
  "marked_at": "2025-02-15T10:30:45Z",
  "marked_by_face": true
}
```

### GET /api/v1/face/status

Get face engine capabilities.

**Response:**
```json
{
  "available": true,
  "embedding_threshold": 0.60,
  "confidence_threshold": 0.65,
  "embedding_dimension": 128,
  "model": "ResNet-based (face_recognition library)",
  "detection_model": "CNN (MMOD)"
}
```

## References

- face_recognition: https://github.com/ageitgey/face_recognition
- MediaPipe: https://mediapipe.dev/
- OpenCV: https://opencv.org/
"""

# This is documentation - no code generated
