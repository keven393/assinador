FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# System deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpq-dev curl ca-certificates wget \
 && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy app
COPY . .

# Create directories expected by app
RUN mkdir -p logs temp_files pdf_assinados keys

# Create non-root user
# Vamos aceitar UIDs/GIDs do docker-compose para evitar problemas de permissão
ARG HOST_UID=1000
ARG HOST_GID=1000

RUN groupadd -f -g $HOST_GID appuser && \
    useradd -u $HOST_UID -g $HOST_GID -m -s /bin/bash appuser && \
    chown -R appuser:appuser /app

USER appuser

# Env defaults (override in docker-compose)
ENV FLASK_ENV=production \
    FLASK_DEBUG=False \
    HOST=0.0.0.0 \
    PORT=5001

EXPOSE 5001

# Run with gunicorn
CMD ["gunicorn", "--workers", "4", "--bind", "0.0.0.0:5001", "asgi:app"]
