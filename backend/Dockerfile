# Multi-stage: build optional deps then run
FROM python:3.11-slim as base

WORKDIR /app

# System deps for MySQL and optional face_recognition (dlib)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    default-libmysqlclient-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Optional: install face_recognition (uncomment if you need it in Docker)
# RUN apt-get update && apt-get install -y --no-install-recommends cmake \
#     && pip install --no-cache-dir face-recognition \
#     && rm -rf /var/lib/apt/lists/*

COPY . .
ENV PYTHONPATH=/app
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
