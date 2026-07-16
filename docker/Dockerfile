# syntax=docker/dockerfile:1

# ---------- Stage 1: builder ----------
FROM python:3.11-slim AS builder

WORKDIR /build
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# ---------- Stage 2: runtime ----------
FROM python:3.11-slim

# Run as a non-root user (Trivy/CIS best practice)
RUN addgroup --system app && adduser --system --ingroup app app

WORKDIR /app
COPY --from=builder /install /usr/local
COPY app/ ./app/

ENV FLASK_ENV=production \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

USER app
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=3s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health')" || exit 1

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "2", "--access-logfile", "-", "app.main:app"]
