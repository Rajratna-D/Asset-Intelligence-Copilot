# ==========================================
# Stage 1: Build the React + Vite Frontend
# ==========================================
FROM node:20-alpine AS frontend-builder
WORKDIR /app/frontend

COPY frontend/package*.json ./
RUN npm ci

COPY frontend/ ./
RUN npm run build

# ==========================================
# Stage 2: Python FastAPI Production Backend
# ==========================================
FROM python:3.11-slim AS production

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000

WORKDIR /app

# Install system dependencies if required
RUN apt-get update && apt-get install -y --no-install-recommends \
    sqlite3 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code, dataset, and configuration
COPY backend/ ./backend/
COPY sample-data/ ./sample-data/
COPY 01-problem-statement.md 02-dataset-guide.md 03-evaluation-queries.md 04-prerequisites.md MASTER_PROJECT_SPEC.md ./

# Copy compiled frontend from Stage 1 into frontend/dist/
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist

# Initialize & Ingest SQLite Database during build so startup is instantaneous
RUN python -m backend.db.ingest

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/api/dashboard || exit 1

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
