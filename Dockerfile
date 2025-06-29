# ---- Base image -------------------------------------------------------------
FROM python:3.9-slim

# ---- Environment ------------------------------------------------------------
ENV PYTHONUNBUFFERED=1 \
  PYTHONDONTWRITEBYTECODE=1 \
  APP_HOME=/app \
  PORT=8080

# ---- OS packages ------------------------------------------------------------
RUN apt-get update && apt-get install -y --no-install-recommends \
  gcc \
  curl &&
  rm -rf /var/lib/apt/lists/*

# ---- App setup --------------------------------------------------------------
WORKDIR ${APP_HOME}

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip &&
  pip install --no-cache-dir -r requirements.txt

COPY . .

# ---- Permissions / non‑root user -------------------------------------------
RUN chmod +x start.sh &&
  adduser --disabled-password --gecos '' appuser &&
  chown -R appuser:appuser "${APP_HOME}"

USER appuser

# ---- Runtime config ---------------------------------------------------------
EXPOSE ${PORT}

HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:${PORT}/health || exit 1

CMD ["./start.sh"]
