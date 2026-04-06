# DatasetLoader - Automatic Face Dataset Scanner

Professional dataset loader for face recognition. Automatically scans student folders, extracts face encodings, and handles errors gracefully.

## Dataset Structure

```
dataset/
├── Student One/
│   ├── face_001.jpg
│   ├── face_002.png
│   ├── image_001.jpg (any image name works)
│   └── ...
├── Student Two/
│   ├── face_001.jpg
│   └── ...
└── ...
```

**Requirements:**
- One folder per student (folder name = student name)
- Images in any format (JPG, JPEG, PNG)
- At least 1 image with a clear face per student

## Usage

### Basic Usage

```python
from ai_attendance.dataset_loader import DatasetLoader

# Create loader (uses default dataset/ path)
loader = DatasetLoader()

# Load embeddings
embeddings = loader.load_embeddings()

# embeddings is Dict[str, np.ndarray]
# Keys: student names
# Values: 128-d face embeddings (averaged)
for name, embedding in embeddings.items():
    print(f"{name}: {embedding.shape}")
```

### With Custom Dataset Path

```python
from pathlib import Path
from ai_attendance.dataset_loader import DatasetLoader

loader = DatasetLoader(dataset_path=Path("my_dataset"))
embeddings = loader.load_embeddings()
```

### Get Statistics

```python
loader = DatasetLoader()
embeddings = loader.load_embeddings()

stats = loader.get_statistics()
print(f"Processed: {stats['total_images_processed']} images")
print(f"Found valid faces for: {stats['students_with_valid_faces']} students")
print(f"Skipped: {stats['total_images_skipped']} images")

# Per-student stats
for name, per_student in stats['per_student'].items():
    print(f"{name}: {per_student['images_processed']} processed")
```

### Get Student List

```python
loader = DatasetLoader()
students = loader.get_student_list()
print(f"Students: {students}")
```

## Class Reference

### `DatasetLoader(dataset_path=config.DATASET_PATH)`

Initialize loader with dataset path.

**Parameters:**
- `dataset_path` (Path | str): Path to dataset root directory

**Raises:**
- `FileNotFoundError`: If dataset path doesn't exist
- `RuntimeError`: If face_recognition library not installed

---

### `load_embeddings() -> Dict[str, np.ndarray]`

Scan dataset and compute averaged face embeddings.

**Process:**
1. Discover all student folders
2. For each student:
   - Find all images (JPG, JPEG, PNG)
   - Load images (limits to 10 per student for performance)
   - Detect faces using HOG model
   - Extract 128-d encodings from valid faces
   - Average encodings to create student template
3. Return mapping of student → embedding

**Returns:**
- `Dict[str, np.ndarray]`: Student name → averaged 128-d embedding

**Raises:**
- `DatasetLoaderError`: If dataset invalid or no students found

**Logging:**
- ✓ INFO: Dataset scan start/completion
- ✓ INFO: Per-student processing
- ✓ DEBUG: Image processing details
- ✓ WARNING: Students with no valid faces
- ✓ INFO: Comprehensive summary with statistics

**Example Output:**
```
INFO: starting dataset scan: 45 student(s) found
INFO: processing student: Alice
DEBUG:   found 8 image(s)
DEBUG:   face_001.jpg: face encoding extracted
DEBUG:   face_002.jpg: face encoding extracted
DEBUG:   ...
INFO:   Alice: loaded 5 valid encoding(s), created averaged embedding
...
INFO: =====================================================================
INFO: DATASET LOAD SUMMARY
INFO: =====================================================================
INFO: Dataset Path:          /<path>/dataset
INFO: Total Students:        45
INFO:   - With valid faces:  44
INFO:   - No valid faces:    1
INFO: Total Images Found:    320
INFO:   - Processed:         268
INFO:   - Skipped:           52
INFO: Process Rate:          83.8%
WARNING: Students with issues:
WARNING:   - John Doe: No Valid Faces (found=2, processed=0, skipped=2)
INFO: =====================================================================
```

---

### `get_statistics() -> Dict`

Return dataset loading statistics.

**Returns:**
```python
{
    "total_students": int,
    "total_images_found": int,
    "total_images_processed": int,
    "total_images_skipped": int,
    "students_with_valid_faces": int,
    "students_with_no_faces": int,
    "per_student": {
        "Student Name": {
            "images_found": int,
            "images_processed": int,
            "images_skipped": int,
            "reason": "success" | "no_images" | "no_valid_faces",
        },
        ...
    }
}
```

---

### `get_student_list() -> List[str]`

Get sorted list of all discovered student directories.

**Returns:**
- `List[str]`: Student names (sorted alphabetically)

---

## Error Handling

### DatasetLoaderError

Raised when dataset cannot be loaded.

```python
from ai_attendance.dataset_loader import DatasetLoader, DatasetLoaderError

try:
    loader = DatasetLoader()
    embeddings = loader.load_embeddings()
except DatasetLoaderError as e:
    print(f"Dataset load failed: {e}")
    # Handle gracefully: use cached embeddings, ask user to provide dataset, etc.
```

---

## Performance Notes

- **Image Limit**: Max 10 images per student (configurable by editing source)
- **Face Detection**: Uses HOG model (CPU-fast, not GPU)
- **Encoding**: ResNet-based, always 128-d vector
- **Averaging**: Per-student embeddings are averaged from all valid images
- **Typical Speed**: ~1-2 seconds per 100 images on modern CPU

---

## Features

✅ **Automatic Directory Discovery** - Finds all student folders  
✅ **Flexible Image Names** - Any JPG/PNG filename works  
✅ **Face Detection** - Ignores/skips images with 0 or multiple faces  
✅ **Error Resilience** - Continues processing if single image fails  
✅ **Statistics Tracking** - Detailed per-student and global metrics  
✅ **Comprehensive Logging** - DEBUG, INFO, WARNING levels  
✅ **Production-Grade** - Handles edge cases, exceptions, validations  

---

## Common Issues

### "No student folders found in dataset"

**Cause:** Dataset folder is empty.  
**Fix:** Create student folders:
```
dataset/
├── Alice/
│   └── face_001.jpg
└── Bob/
    └── face_001.jpg
```

### "Student XYZ had no valid face images"

**Cause:** Images don't contain exactly one face per image.  
**Fix:** Provide clear photos with exactly one face per image.

### "No face detected" (DEBUG log)

**Cause:** Common - images without faces are expected  
**Action:** Nothing - loader automatically skips them

### Slow startup

**Cause:** Many images in dataset.  
**Fix:** Limit images per student (edit `load_embeddings()` to load fewer than 10 images)

---

## Integration

Used by `FaceRecognitionEngine`:

```python
from ai_attendance.face_engine import FaceRecognitionEngine

engine = FaceRecognitionEngine()
engine.initialize()  # Internally uses DatasetLoader
```
