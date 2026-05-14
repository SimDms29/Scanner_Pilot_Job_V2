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

# Chromium système (évite le CDN Playwright inaccessible en prod)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    chromium \
    && rm -rf /var/lib/apt/lists/*

# Playwright utilise le chromium système
ENV PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1
ENV PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH=/usr/bin/chromium

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
