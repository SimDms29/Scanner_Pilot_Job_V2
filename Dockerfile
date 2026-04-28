# ── Stage 1 : build du frontend React ───────────────────────────────────────
FROM node:20-alpine AS frontend-build
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# ── Stage 2 : backend FastAPI ────────────────────────────────────────────────
FROM python:3.11-slim
WORKDIR /app/backend

# Dépendances système minimales
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Dépendances Python
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Code backend
COPY backend/ ./

# Frontend buildé (servi comme static files par FastAPI)
COPY --from=frontend-build /app/frontend/dist /app/frontend/dist

# Répertoire de données persistantes (monté en volume)
RUN mkdir -p /app/data

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
