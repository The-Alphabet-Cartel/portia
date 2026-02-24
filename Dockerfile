# ============================================================================
# Portia Bot - Dockerfile
# ============================================================================
# FILE VERSION: v1.0.0
# Repository: https://github.com/the-alphabet-cartel/portia
# Community: The Alphabet Cartel - https://discord.gg/alphabetcartel
# ============================================================================

# ============================================================================
# Stage 1: Builder
# ============================================================================
FROM python:3.12-slim AS builder

WORKDIR /build

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# ============================================================================
# Stage 2: Runtime
# ============================================================================
FROM python:3.12-slim AS runtime

ARG DEFAULT_UID=1000
ARG DEFAULT_GID=1000

ENV PATH="/opt/venv/bin:$PATH"
ENV PYTHONPATH="/app"

# Install tini for signal handling + groupmod/usermod utilities
RUN apt-get update && apt-get install -y --no-install-recommends \
    tini \
    passwd \
    && rm -rf /var/lib/apt/lists/*

# Create default app user (entrypoint will adjust UID/GID at runtime)
RUN groupadd -g ${DEFAULT_GID} appgroup && \
    useradd -m -u ${DEFAULT_UID} -g ${DEFAULT_GID} appuser

# Copy venv from builder
COPY --from=builder /opt/venv /opt/venv

# Set working directory and copy source
WORKDIR /app
COPY src/ ./src/
COPY docker-entrypoint.py ./docker-entrypoint.py

# Create runtime directories
RUN mkdir -p /app/logs /app/data && \
    chown -R appuser:appgroup /app

# NOTE: No USER directive — entrypoint handles privilege dropping at runtime
ENTRYPOINT ["/usr/bin/tini", "--", "python", "/app/docker-entrypoint.py"]
CMD ["python", "src/main.py"]
