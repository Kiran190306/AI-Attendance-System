Backend environment & running (production)
========================================

Copy `backend/.env.example` to `backend/.env` and update values before running.

Recommended steps (example using virtualenv):

```bash
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\Activate.ps1
pip install -r backend/requirements.txt
# Set env file or export variables
uvicorn app.main:app --host 0.0.0.0 --port 8000 --factory
```

Notes:
- The application reads `.env` in the backend folder using pydantic Settings.
- Logging is structured (JSON) by default when `DEBUG=false`.
- For production, run behind a process manager (systemd) or use Docker Compose.
