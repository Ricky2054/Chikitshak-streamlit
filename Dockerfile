# Build stage: frontend
FROM node:20-alpine AS frontend-build
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
ENV VITE_API_URL=
RUN npm run build

# Runtime stage: Python backend + built frontend
FROM python:3.11-slim
WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
COPY --from=frontend-build /app/frontend/dist ./frontend/dist

ENV PYTHONUNBUFFERED=1
ENV LLM_PROVIDER=openrouter
ENV EMBEDDING_PROVIDER=local
ENV DISABLE_AUTH=1
ENV PORT=8000

EXPOSE 8000

CMD ["sh", "-c", "uvicorn app:api --host 0.0.0.0 --port ${PORT:-8000}"]
