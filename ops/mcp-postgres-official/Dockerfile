# Dockerfile for Official PostgreSQL MCP Server (crystaldba/postgres-mcp)
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    libpq-dev \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install the official postgres-mcp package
RUN pip install --no-cache-dir git+https://github.com/crystaldba/postgres-mcp.git

# Expose port
EXPOSE 8001

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8001/health || exit 1

# Run the MCP Postgres server
CMD ["python", "-m", "postgres_mcp", "--host", "0.0.0.0", "--port", "8001"]
