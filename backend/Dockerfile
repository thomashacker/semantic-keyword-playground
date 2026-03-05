FROM python:3.12-slim

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

# Copy dependency files first for layer caching
COPY pyproject.toml .
COPY uv.lock* .

# Install dependencies (no dev deps in production)
RUN uv sync --no-dev --frozen 2>/dev/null || uv sync --no-dev

# Copy application code only (data/ and scripts/ are for local seeding only)
COPY app/ app/

# Expose port
EXPOSE 8000

# Run with uv
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
