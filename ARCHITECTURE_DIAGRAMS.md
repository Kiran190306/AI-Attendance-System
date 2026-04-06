"""
VISUAL ARCHITECTURE DIAGRAM
Face Recognition System v2.0
"""

# =============================================================================
# SYSTEM OVERVIEW
# =============================================================================

"""
┌─────────────────────────────────────────────────────────────────────────┐
│                    AI ATTENDANCE SYSTEM v2.0                            │
│                  Real Face Recognition with Embeddings                  │
└─────────────────────────────────────────────────────────────────────────┘

                              ┌─────────────┐
                              │ CAMERA FEED │
                              │  (RT Video) │
                              └──────┬──────┘
                                     │
         ┌───────────────────────────┼───────────────────────────┐
         │                           │                           │
         ▼                           ▼                           ▼
    ┌─────────┐              ┌──────────────┐          ┌─────────────┐
    │ Real-   │              │  API         │          │  Dataset    │
    │ Time    │              │  Endpoint    │          │  Processor  │
    │ System  │              │  /face/mark  │          │             │
    └────┬────┘              └──────┬───────┘          └─────┬───────┘
         │                          │                        │
         └──────────┬───────────────┼────────────┬───────────┘
                    │               │            │
              ┌─────▼────────────────▼───────┬───▼──────────┐
              │                              │              │
         ┌────▼─────────────────────────────▼────┐          │
         │     EMBEDDINGS RECOGNITION ENGINE     │          │
         │                                       │          │
         │  • Extract 128-d embeddings          │          │
         │  • Distance-based matching           │          │
         │  • Confidence scoring                │          │
         │  • Vectorized operations             │          │
         └────┬──────────────────────────────────┘          │
              │                                              │
              ▼                                              ▼
        ┌──────────────┐                           ┌────────────────┐
        │ RECOGNITION  │                           │ DATASET        │
        │ RESULT       │                           │ MANAGEMENT     │
        │              │                           │                │
        │ ✓ Matched    │                           │ • Capture      │
        │ ✗ Unknown    │                           │ • Generate     │
        │ ? Low conf   │                           │ • Validate     │
        └──────┬───────┘                           │ • Store        │
               │                                   └────────┬───────┘
               ▼                                           │
        ┌──────────────────────────┐                      │
        │  DATABASE UPDATE         │◄─────────────────────┘
        │  • Student record        │
        │  • Attendance mark       │
        │  • Embeddings stored     │
        └──────────────────────────┘
"""

# =============================================================================
# DATA FLOW - Real-Time Attendance
# =============================================================================

"""
REAL-TIME FACE RECOGNITION FLOW:

┌────────────────────┐
│ Camera Frame       │
│ (BGR image)        │
└────────┬───────────┘
         │
         ▼
┌────────────────────────────────┐
│ MediaPipe Face Detection       │
│ ---------------------------    │
│ • Detect face locations        │
│ • Get bounding boxes           │
│ • Filter small faces           │
└────────┬───────────────────────┘
         │
         ├─ No face ──────────────────┐
         │                            │
    Face(es) ┌──────────────────────────────┐
    Detected │ Extract Face ROI + Crop      │
             │ Convert BGR → RGB            │
             │ Prepare for encoding         │
             └──────┬─────────────────────────┘
                    │
                    ▼
          ┌──────────────────────────┐
          │ face_recognition Extractor
          │ (ResNet-based 128-d)     │
          │                          │
          │ Input: RGB face crop     │
          │ Output: 128-d embedding  │
          └──────┬───────────────────┘
                 │
                 ▼
          ┌──────────────────────────┐
          │ Load Stored Embeddings   │
          │ from Database            │
          │                          │
          │ {student_id: embedding}  │
          │ × N students             │
          └──────┬───────────────────┘
                 │
                 ▼
          ┌──────────────────────────────────┐
          │ Vectorized Distance Computation  │
          │                                  │
          │ distances = ||live - stored||₂   │
          │ for all stored embeddings        │
          │                                  │
          │ Result: array of distances       │
          └──────┬───────────────────────────┘
                 │
                 ▼
          ┌──────────────────────────┐
          │ Find Minimum Distance   │
          │ & Check Threshold       │
          │                          │
          │ if dist <= 0.60:        │
          │   confidence = 1-(d/thr) │
          │ else:                    │
          │   confidence = 0         │
          └──────┬────────────────────┘
                 │
         ┌───────┴────────┬────────────┐
         │                │            │
    Match ✓           No Match ✗    Low Conf ?
    (high conf)       (dist > 0.6)   (conf < 0.65)
         │                │            │
         ▼                ▼            ▼
    ┌─────────┐     ┌──────────┐  ┌───────────┐
    │ GREEN   │     │ RED      │  │ YELLOW    │
    │ BOX     │     │ BOX      │  │ BOX       │
    │ + Name  │     │ Unknown  │  │ Retry     │
    └────┬────┘     └──┬───────┘  └─────┬─────┘
         │             │                │
    MARK ATT.      NO ACTION        NO ACTION
         │
         ▼
    ┌──────────────────────┐
    │ Database Update      │
    │ attendance marked = ✓│
    └──────────────────────┘
"""

# =============================================================================
# DATABASE SCHEMA
# =============================================================================

"""
STUDENT TABLE (Enhanced):

┌─ Student ──────────────────────┐
│ ─────────────────────────────── │
│ id (PK)                   INT   │
│ student_id (UNIQUE)      STR   │
│ full_name                STR   │
│ email                    STR   │
│                                │
│ [NEW] face_embedding    BYTES  │ ← 512 bytes (128×float32)
│ [NEW] embeddings_count   INT   │ ← Source images count
│ [NEW] embeddings_updated DT    │ ← Last update timestamp
│                                │
│ is_active               BOOL   │
│ created_at             DT      │
│ updated_at             DT      │
└────────────────────────────────┘
         │
         ├──► Attendance (1:M)
         │
         └──► RecognitionLog (1:M) [optional]

"""

# =============================================================================
# COMPONENT INTERACTION DIAGRAM
# =============================================================================

"""
┌──────────────────────────────────────────────────────────────────────┐
│                         FRONTEND (React)                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐               │
│  │ Live Camera  │  │ Capture Btn  │  │ Recognition │               │
│  │ Component    │  │              │  │ UI Component │               │
│  └──────┬───────┘  └──────┬───────┘  └──────▲───────┘               │
│         │                 │                 │                        │
│         └─────────────────┼─────────────────┘                        │
│                           │                                          │
├───────────────────────────┼──────────────────────────────────────────┤
│                  HTTP/JSON API (localhost:8000)                      │
│                getImage() → base64 → POST /api/v1/face/mark         │
│                ← JSON response with recognition results             │
├───────────────────────────┼──────────────────────────────────────────┤
│                    BACKEND (FastAPI)                              │
│  ┌─────────────────────────░────────────────────────────┐            │
│  │           API Route: /api/v1/face/mark              │            │
│  │  ┌──────────────────────────────────────────────┐  │            │
│  │  │ 1. Validate image data                       │  │            │
│  │  │ 2. Extract 128-d embedding                   │  │            │
│  │  │ 3. Load student embeddings from DB           │  │            │
│  │  │ 4. Compute distances (vectorized)            │  │            │
│  │  │ 5. Find minimum distance                     │  │            │
│  │  │ 6. Check confidence >= 0.65                  │  │            │
│  │  │ 7. Mark attendance in DB                     │  │            │
│  │  │ 8. Return response                           │  │            │
│  │  └──────────────────────────────────────────────┘  │            │
│  └────────────────────────┬──────────────────────────────┘            │
│                           │                                          │
│              ┌────────────┴────────────┐                             │
│              ▼                         ▼                             │
│     ┌─────────────────┐       ┌──────────────────┐                  │
│     │  face_engine.py │       │  models/student  │                  │
│     │  • Recognition  │       │  • face_embedding│                  │
│     │  • Matching     │       │  • get_embedding │                  │
│     │  • Scoring      │       │  • has_valid()  │                  │
│     └─────────────────┘       └──────────────────┘                  │
│              │                         │                            │
│              └────────────┬────────────┘                             │
│                           ▼                                          │
│              ┌─────────────────────────┐                             │
│              │   MySQL Database        │                             │
│              │  • Students (with emb)  │                             │
│              │  • Attendance records   │                             │
│              │  • Sessions             │                             │
│              └─────────────────────────┘                             │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
"""

# =============================================================================
# DATASET PROCESSING PIPELINE
# =============================================================================

"""
DATASET GENERATION FLOW:

┌────────────────────┐
│ Raw Dataset        │
│                    │
│ dataset/           │
│ ├─ John Doe/       │
│ │  ├─ face_001.jpg │
│ │  ├─ face_002.jpg │
│ │  └─ ...          │
│ └─ Jane Smith/     │
│    └─ ...          │
└────────┬───────────┘
         │
         ▼
┌────────────────────────────────┐
│ Validation                     │
│ • Check directory structure    │
│ • Validate image formats       │
│ • Check file naming            │
└────────┬───────────────────────┘
         │
    ✓ Valid
         │
         ▼
┌────────────────────────────────────┐
│ Load & Parse Images                │
│ • face_recognition.load_image()   │
│ • Detect face locations            │
│ • Validate: exactly 1 face         │
└────────┬───────────────────────────┘
         │
    Invalid images → Skipped (logged)
         │
         ▼
┌────────────────────────────────────┐
│ Extract Embeddings                 │
│ • face_recognition.face_encodings()│
│ • Output: 128-d vector (float32)   │
│ • Per image                        │
└────────┬───────────────────────────┘
         │
         ▼
┌────────────────────────────────────┐
│ Average Embeddings                 │
│ • Collect all per student          │
│ • Mean across all images           │
│ • Output: 1 embedding per student  │
└────────┬───────────────────────────┘
         │
         ▼
┌────────────────────────────────────┐
│ Store in Database                  │
│ • Convert 128-d to bytes (512 B)  │
│ • Store in Student.face_embedding  │
│ • Update embeddings_count & _at    │
└────────┬───────────────────────────┘
         │
         ▼
┌────────────────────────────────────┐
│ Verification                       │
│ • Count valid embeddings           │
│ • List enrolled students           │
│ • Check database integrity         │
└────────────────────────────────────┘
"""

# =============================================================================
# PERFORMANCE CHARACTERISTICS
# =============================================================================

"""
TIMING BREAKDOWN (per face recognition):

┌──────────────────────────────────────────────┐
│ Face Detection (MediaPipe)                   │
│ ─────────────────────────────────            │
│ Input: Full frame                            │
│ Time: 30-50ms                                │
│ Output: Face bounding boxes                  │
└──────────────────────┬───────────────────────┘
                       │
┌──────────────────────▼───────────────────────┐
│ Embedding Extraction (face_recognition)     │
│ ─────────────────────────────────────────── │
│ Input: Face crop                             │
│ Time: 20-40ms                                │
│ Output: 128-d vector                         │
└──────────────────────┬───────────────────────┘
                       │
┌──────────────────────▼───────────────────────┐
│ Distance Computation (vectorized)            │
│ ─────────────────────────────────────────── │
│ Input: 1 live embedding, N stored           │
│ Time: 5-10ms (N=50-100 students)            │
│ Output: List of distances                    │
└──────────────────────┬───────────────────────┘
                       │
┌──────────────────────▼───────────────────────┐
│ Matching & Scoring                           │
│ ─────────────────────────────────────────── │
│ Input: Distances                             │
│ Time: <1ms                                   │
│ Output: Student ID + confidence              │
└──────────────────────────────────────────────┘

TOTAL: 50-100ms per recognition
       10-20 FPS sustainable rate
"""

# =============================================================================
# ERROR HANDLING FLOW
# =============================================================================

"""
ERROR DETECTION & HANDLING:

Request → Validate Input
           │
      ├─ Invalid image data ──────────────────► Error Response
      │
      ├─ Image decode fails ──────────────────► Error Response
      │
      ▼
Extract Embedding
│
├─ No face detected ────────────────────────► Error Response
│
├─ Multiple faces ──────────────────────────► Process all (or error)
│
├─ Extraction fails ───────────────────────► Error Response
│
▼
Load from Database
│
├─ DB connection error ────────────────────► Error Response
│
├─ No students with embeddings ───────────► Error Response
│
▼
Compute Distances
│
├─ Math error ─────────────────────────────► Error Response
│
▼
Check Confidence
│
├─ No match (dist > 0.60) ────────────────► "Unknown" Response
│
├─ Low confidence (conf < 0.65) ─────────► Validation Error
│
▼
Mark Attendance
│
├─ Already marked ─────────────────────────► Conflict Error
│
├─ Session not found ──────────────────────► Not Found Error
│
├─ DB write error ─────────────────────────► Error Response
│
▼
Success ✓
"""

print(__doc__)
