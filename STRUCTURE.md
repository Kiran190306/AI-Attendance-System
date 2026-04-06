# Project structure (production-ready)

Refactored into **four main layers**: recognition, database, API, frontend.

## Layer overview

| Layer        | Path            | Role |
|-------------|------------------|------|
| **Recognition** | `modules/recognition/` | Face capture (OpenCV) and real-time attendance (MediaPipe + OpenCV LBPH). Runnable standalone; optional use from API. |
| **Database**    | `modules/database/`   | SQLite attendance storage (`attendance_db`) and reports (`attendance_reports`). Used by API for dashboard records. |
| **API**         | `backend/`            | FastAPI app: MySQL (main app data), JWT auth, sessions/students/face/reports; imports `modules/database` for `/api/v1/records`. |
| **Frontend**    | `frontend/`           | React (Vite) SPA; consumes API only. |

## Directory layout

```
AI-Attendance-System/
├── modules/
│   ├── recognition/
│   │   ├── face_capture/          # dataset/<name>/ face images
│   │   └── realtime_attendance/   # live camera → CSV log
│   └── database/
│       ├── attendance_db/         # SQLite: insert/fetch, no duplicate/day
│       └── attendance_reports/    # daily report, monthly %, CSV export
├── backend/                       # FastAPI
│   ├── app/
│   │   ├── api/v1/
│   │   ├── core/
│   │   ├── models/
│   │   └── schemas/
│   └── ...
├── frontend/                      # React
│   └── src/
├── docker-compose.yml
├── .env.example
├── README.md
└── STRUCTURE.md (this file)
```

## Dependencies between layers

- **API** → **Database**: backend adds `modules/database` to `sys.path` and imports `attendance_db`, `attendance_reports` for records endpoints.
- **Frontend** → **API**: all data via REST; no direct use of recognition or database.
- **Recognition** → **Database**: optional; `realtime_attendance` can be extended to write to `attendance_db`; by default it writes to CSV.

## Running components

- **Backend**: From `backend/`, run `uvicorn app.main:app`. Project root (parent of `backend`) must exist so `modules/database` can be resolved.
- **Recognition** (standalone): From project root, set `PYTHONPATH=modules/recognition` and run `python -m face_capture` or `python -m realtime_attendance`.
- **Database** (standalone): Set `PYTHONPATH=modules/database` and `import attendance_db` / `attendance_reports` in scripts.

## Scalability

- Recognition and database are **separate packages**; they can be versioned, tested, or replaced independently.
- API stays a single service; it can later call recognition/database as internal libs or as separate services if needed.
- Frontend remains a single SPA; can be split by route or micro-frontend later if required.
