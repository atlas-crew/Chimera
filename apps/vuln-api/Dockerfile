# Starlette/uvicorn application for the Chimera WAF Demo API (dev)
FROM python:3.12-slim

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Set working directory
WORKDIR /app

# Copy dependency files
COPY pyproject.toml uv.lock /app/

# Install dependencies using uv
RUN uv sync --frozen --no-dev

# Copy application package and static assets
COPY app/ /app/app/
COPY static /app/static

# Expose port 80 for internal access
EXPOSE 80

ENV PORT=80

# Note: running as root is acceptable for this demo/honeypot environment
CMD ["uv", "run", "uvicorn", "app.asgi:app", "--host", "0.0.0.0", "--port", "80", "--reload"]
