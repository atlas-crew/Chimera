# Flask application for  WAF Demo API endpoints
FROM python:3.12-slim

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Set working directory
WORKDIR /app

# Copy dependency files
COPY pyproject.toml uv.lock /app/

# Install dependencies using uv
RUN uv sync --frozen --no-dev

# Copy Flask application package, entry point, and static files
COPY app/ /app/app/
COPY app.py /app/app.py
COPY static /app/static

# Expose port 80 for internal access
EXPOSE 80

# Set environment variable for Flask port
ENV PORT=80

# Run Flask application
# Note: Running as root is acceptable for this demo/honeypot environment
CMD ["uv", "run", "python", "app.py"]
