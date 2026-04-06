# System Architecture

The AI Attendance System is composed of several interconnected modules:

1. **Camera Input** – captures live video streams from one or more cameras.
2. **Face Recognition Engine** – processes frames, detects faces, and compares
   them against stored embeddings.
3. **Attendance Service** – records recognised identities along with
   timestamps and camera IDs; handles duplicate suppression.
4. **Database / CSV Storage** – attendance records are persisted in a CSV file
   and optionally a database for long-term storage and querying.
5. **Web Dashboard** – provides a browser-based interface for monitoring
   attendance, viewing analytics and exporting data.

Each component runs in its own thread or process where appropriate. The
recognition engine is shared across cameras to conserve memory. An event bus
facilitates communication between camera threads and the attendance service.