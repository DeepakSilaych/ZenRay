FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY pyproject.toml README.md ./

# Install Python dependencies
RUN pip install --no-cache-dir .

# Copy application code
COPY app/ ./app/

# Port from env (default 4003)
ARG PORT=4003
ENV XRAY_PORT=${PORT}
EXPOSE ${PORT}

# Run server with port from env
CMD uvicorn app.main:app --host 0.0.0.0 --port ${XRAY_PORT:-4003}
