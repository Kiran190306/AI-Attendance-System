# Getting Started - AI Attendance System

Complete setup and deployment guide for the production-ready AI Attendance System.

## Prerequisites

- Python 3.10 or higher
- Webcam (USB or built-in)
- Windows/Linux/Mac with OpenCV support
- ~500MB free disk space (for dependencies)

## Step 1: Verify Installation

Check that all required packages are installed:

```bash
pip list | grep -E "opencv|face-recognition|mediapipe|numpy"
```

Expected output:
```
face-recognition 1.3.0
mediapipe 0.10.x
opencv-python 4.x.x
numpy 1.24.x
```

If any are missing:

```bash
pip install opencv-python face-recognition mediapipe numpy
```

## Step 2: Prepare Dataset

### Create Student Folders

The system learns faces from images in the `dataset/` folder. Create folders for each student:

```
dataset/
├── Alice/
├── Bob/
├── Charlie/
└── ...
```

Replace "Alice", "Bob", "Charlie" with actual student names.

### Add Face Images

For each student, add 3-5 clear photos of their face:

```
dataset/
├── Alice/
│   ├── alice_001.jpg
│   ├── alice_002.jpg
│   ├── alice_003.jpg
│   └── alice_004.jpg
├── Bob/
│   ├── bob_001.jpg
│   ├── bob_002.jpg
│   └── bob_003.jpg
└── Charlie/
    ├── charlie_001.jpg
    ├── charlie_002.jpg
    └── charlie_003.jpg
```

### Image Requirements

✓ **Clear, well-lit photos** (frontal face, not blurry)  
✓ **Exactly one face per image** (system skips multi-face images)  
✓ **Multiple angles** (helps recognition accuracy)  
✓ **Supported formats:** JPG, JPEG, PNG  
✗ **Avoid:** Extremely dark/bright, extreme angles, masks/sunglasses  

### Pro Tips

- Use different lighting conditions (natural light, indoor lighting)
- Vary facial expressions (neutral, slight smile)
- Include images with different hairstyles if applicable
- Minimum 3 images per student recommended
- Maximum 10 images per student will be used by the system

## Step 3: Configure System (Optional)

Edit `ai_attendance/config.py` to customize:

```python
# Face recognition confidence threshold (0.0 to 1.0)
# Lower = more sensitive (more false positives)
# Higher = more strict (may miss faces)
CONFIDENCE_THRESHOLD = 0.50

# Real-time processing optimization
TARGET_FRAME_WIDTH = 640      # Resize frames for speed (decrease for slower hardware)
FRAME_SKIP = 2                 # Process every Nth frame (increase for slow systems)
DETECTION_SCALE = 0.5          # Face detection resolution scale
```

### Performance Tuning

| Hardware | Recommendation |
|----------|-----------------|
| Fast CPU (recent i7/Ryzen) | TARGET_FRAME_WIDTH=800, FRAME_SKIP=1 |
| Mid-range CPU | TARGET_FRAME_WIDTH=640, FRAME_SKIP=2 |
| Slower CPU | TARGET_FRAME_WIDTH=480, FRAME_SKIP=3 |

## Step 4: Run the System

### Start Attendance

```bash
cd d:\AI-Attendance-System
python attendance_system.py
```

### First Run

On first run, the system will:

1. ✓ Scan the `dataset/` folder
2. ✓ Load student face images
3. ✓ Extract face embeddings (128-d vectors)
4. ✓ Create `attendance/attendance.csv` file
5. ✓ Initialize MediaPipe face detector
6. ✓ Open your camera

**Console Output (Expected):**
```
INFO:ai_attendance.dataset_loader:Starting dataset scan: 3 student(s) found
INFO:ai_attendance.dataset_loader:processing student: Alice
DEBUG:ai_attendance.dataset_loader:  found 4 image(s)
DEBUG:ai_attendance.dataset_loader:  alice_001.jpg: face encoding extracted
DEBUG:ai_attendance.dataset_loader:  alice_002.jpg: face encoding extracted
DEBUG:ai_attendance.dataset_loader:  alice_003.jpg: face encoding extracted
DEBUG:ai_attendance.dataset_loader:  alice_004.jpg: face encoding extracted
INFO:ai_attendance.dataset_loader:  Alice: loaded 4 valid encoding(s), created averaged embedding
...
INFO:ai_attendance.main:=====================================================================
INFO:ai_attendance.main:DATASET LOAD SUMMARY
INFO:ai_attendance.main:=====================================================================
INFO:ai_attendance.main:Dataset Path:          d:\AI-Attendance-System\dataset
INFO:ai_attendance.main:Total Students:        3
INFO:ai_attendance.main:  - With valid faces:  3
INFO:ai_attendance.main:  - No valid faces:    0
INFO:ai_attendance.main:Total Images Found:    12
INFO:ai_attendance.main:  - Processed:         12
INFO:ai_attendance.main:  - Skipped:           0
INFO:ai_attendance.main:Process Rate:          100.0%
INFO:ai_attendance.main:=====================================================================
INFO:ai_attendance.main:Attendance System Running (Press 'Q' to quit, 'R' to reset)
```

## Step 5: Using the System

### What You'll See

The system displays a live video with:

```
┌─────────────────────────────────────────────┐
│ ATTENDANCE        │    PERFORMANCE          │
│ Recognized: 2     │    FPS: 28              │
│ Unknown: 0        │    Frame: 5ms           │
│ Marked: 2         │    Detect: 4ms          │
│ Duplicates: 0     │    Recog: 1ms           │
│                   │    Students: 3          │
├─────────────────────────────────────────────┤
│ RECENT ACTIVITY                             │
│ 09:30:45 - Alice [OK] MARKED                │
│ 09:31:12 - Bob [OK] MARKED                  │
│ 09:32:33 - Unknown [??] UNKNOWN FACE        │
│                                             │
│ Press 'Q' to quit | 'R' to reset session   │
└─────────────────────────────────────────────┘
```

### Keyboard Controls

- **Q**: Quit the system (shows session summary)
- **R**: Reset session (clears marked count)

### Live Recognition

- **Green boxes** = Recognized student (marked in attendance)
- **Red boxes** = Unknown face (no match found)
- **Yellow boxes** = Duplicate (already marked today)

## Step 6: View Attendance Records

### Option 1: View CSV File

Open `attendance/attendance.csv` in:
- Excel
- Google Sheets
- Notepad (or any text editor)

**CSV Format:**
```
date,time,name,timestamp_iso,confidence
2024-01-15,09:30:45,Alice,2024-01-15T09:30:45.123456,0.95
2024-01-15,09:31:12,Bob,2024-01-15T09:31:12.456789,0.87
2024-01-15,09:32:33,Alice,2024-01-15T09:32:33.789012,0.92
```

### Option 2: Export to Excel

```bash
# Copy CSV to new location
copy attendance\attendance.csv attendance_export.csv

# Open in Excel (double-click)
```

### Option 3: Parse Programmatically

```python
import csv
from datetime import datetime

# Read attendance records
records = []
with open("attendance/attendance.csv", "r", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for row in reader:
        records.append({
            "date": row["date"],
            "time": row["time"],
            "name": row["name"],
            "confidence": float(row["confidence"])
        })

# Analyze
for record in records:
    print(f"{record['date']} {record['time']} - {record['name']} ({record['confidence']:.0%})")
```

## Step 7: Troubleshooting

### Issue: "No student folders found"

**Cause:** Dataset folder is empty  
**Solution:** Create folders in `dataset/` and add images

```bash
# Create example
mkdir dataset\Alice
# Copy face images into dataset\Alice\
```

### Issue: System runs but no faces detected

**Cause 1:** Lighting is too dark  
**Solution:** Improve lighting, move closer to light source

**Cause 2:** Face is too far away  
**Solution:** Move closer to camera (within 2 meters)

**Cause 3:** Face is at extreme angle  
**Solution:** Face camera head-on (not sideways/upside-down)

### Issue: "Student XYZ had no valid face images"

**Cause:** Images for that student don't contain detectable faces  
**Solution:** 
1. Check if images show the student's face clearly
2. Replace with better quality photos
3. Use frontal face images (not profile)

**Debug:** Check what images the system is processing:

```python
from ai_attendance.dataset_loader import DatasetLoader
import logging

# Enable debug logging
logging.getLogger("ai_attendance").setLevel(logging.DEBUG)

# Load
loader = DatasetLoader()
embeddings = loader.load_embeddings()

# Check statistics
stats = loader.get_statistics()
for name, student_stats in stats['per_student'].items():
    print(f"{name}: {student_stats['reason']}")
```

### Issue: Low recognition accuracy

**Cause:** Confidence threshold too low, or poor training images  
**Solutions:**

1. **Increase CONFIDENCE_THRESHOLD:**
```python
# config.py
CONFIDENCE_THRESHOLD = 0.60  # was 0.50
```

2. **Add more diverse training images** to dataset (different angles, lighting)

3. **Retrain:** Delete attendance.csv and restart system to reload dataset

### Issue: "unknown face" too frequent

**Cause:** Unknown people in the video, or threshold too strict  
**Solutions:**

1. **Decrease threshold slightly:**
```python
CONFIDENCE_THRESHOLD = 0.45  # was 0.50
```

2. **Ensure all students are in dataset**

3. **Add more training images** for each student

### Issue: Slow FPS

**Cause:** Hardware too slow, or frame resolution too high  
**Solutions:**

1. **Reduce frame size:**
```python
# config.py
TARGET_FRAME_WIDTH = 480  # was 640
```

2. **Skip more frames:**
```python
# config.py
FRAME_SKIP = 3  # was 2 (process every 3rd frame)
```

3. **Scale down detection:**
```python
# config.py
DETECTION_SCALE = 0.25  # was 0.5
```

## Step 8: Advanced Usage

### Custom Dataset Path

```python
from ai_attendance.dataset_loader import DatasetLoader

loader = DatasetLoader(dataset_path="my_custom_dataset")
embeddings = loader.load_embeddings()
```

### Programmatic API

```python
from ai_attendance.face_engine import FaceRecognitionEngine
from ai_attendance.attendance_service import AttendanceService
import cv2

# Initialize
engine = FaceRecognitionEngine()
engine.initialize()
service = AttendanceService()

# Open camera
cap = cv2.VideoCapture(0)

while True:
    ret, frame = cap.read()
    if not ret:
        break
    
    # Process frame
    results, display = engine.process_frame(frame)
    
    # Mark attendance
    for result in results:
        if result['name'] != 'unknown':
            is_new = service.mark(result['name'], result['confidence'])
            print(f"{result['name']}: {'NEW' if is_new else 'DUPLICATE'}")
    
    # Get stats
    stats = service.get_session_stats()
    
    cv2.imshow("System", display)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
```

### Enable Debug Logging

```bash
# Edit attendance_system.py and add at top:
import logging
logging.getLogger("ai_attendance").setLevel(logging.DEBUG)
```

## System Requirements

| Component | Requirement |
|-----------|-------------|
| Python | 3.10 or higher |
| RAM | 1GB minimum (2GB recommended) |
| CPU | Any modern processor |
| Camera | USB or built-in webcam |
| Disk | 500MB for dependencies + 100MB for dataset |
| OS | Windows/Linux/Mac with OpenCV support |

## Next Steps

1. ✓ Set up Python environment
2. ✓ Prepare dataset with student images
3. ✓ Run attendance_system.py
4. ✓ Monitor console output and logs
5. ✓ View attendance records in CSV

For detailed API documentation, see:
- [ai_attendance/README.md](README.md) - Component overview
- [ai_attendance/DATASET_LOADER.md](DATASET_LOADER.md) - Dataset loader API

---

**Questions?** Check the troubleshooting section or review the console output for detailed error messages.

**Need Help?** Enable debug logging to see detailed processing information.

---

**System Status:** ✅ Production-Ready  
**Version:** 2.0-production
