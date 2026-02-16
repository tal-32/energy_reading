# --- Stage 1: Build Stage ---
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS builder

WORKDIR /app
ENV UV_COMPILE_BYTECODE=1

# Copy workspace configs first for optimal layer caching
COPY pyproject.toml uv.lock README.md ./
COPY shared_lib/pyproject.toml shared_lib/README.md ./shared_lib/
COPY services/frontend/pyproject.toml services/frontend/README.md ./services/frontend/

# Install dependencies into the virtualenv
# Using --package frontend ensures we only grab what this service needs
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-project --no-dev --package frontend

# Copy source code
COPY shared_lib ./shared_lib
COPY services/frontend ./services/frontend

# Final sync to install the workspace projects themselves
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --package frontend

# --- Stage 2: Runtime Stage ---
FROM python:3.12-slim AS runtime

WORKDIR /app

# Setup security
RUN groupadd -r appgroup && useradd -r -g appgroup appuser

# Environment setup
# We include /app so that 'import shared_lib' works seamlessly
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONPATH="/app" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# 1. Copy the virtual environment from builder
COPY --from=builder --chown=appuser:appgroup /app/.venv /app/.venv

# 2. Copy the codebases
COPY --from=builder --chown=appuser:appgroup /app/shared_lib ./shared_lib
COPY --from=builder --chown=appuser:appgroup /app/services/frontend ./services/frontend

USER appuser

# NiceGUI default port
EXPOSE 8080

# Run the frontend from its service directory
CMD ["python", "services/frontend/main.py"]
