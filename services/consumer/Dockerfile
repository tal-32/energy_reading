# --- Stage 1: Build Stage ---
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS builder

WORKDIR /app
ENV UV_COMPILE_BYTECODE=1

# Copy configs first for better caching
COPY pyproject.toml uv.lock README.md ./
COPY shared_lib/pyproject.toml shared_lib/README.md  ./shared_lib/
COPY services/consumer/pyproject.toml services/consumer/README.md ./services/consumer/

# Install dependencies
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-project --no-dev --package consumer

# Copy source code
COPY shared_lib ./shared_lib
COPY services/consumer ./services/consumer

# Final sync installs the workspace projects into /app/.venv
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --package consumer

# --- Stage 2: Runtime Stage ---
FROM python:3.12-slim AS runtime

WORKDIR /app

# Setup security
RUN groupadd -r appgroup && useradd -r -g appgroup appuser

# Environment setup
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONPATH="/app/services/consumer:/app" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# 1. Copy the virtual environment
COPY --from=builder --chown=appuser:appgroup /app/.venv /app/.venv

# 2. Copy ONLY the necessary code (Avoids overwriting .venv with COPY . .)
COPY --chown=appuser:appgroup shared_lib ./shared_lib
COPY --chown=appuser:appgroup services/consumer ./services/consumer

USER appuser
EXPOSE 8000

# Targeted command: Point to the main.py inside the service folder
CMD ["uvicorn", "services.consumer.main:app", "--host", "0.0.0.0", "--port", "8000"]
