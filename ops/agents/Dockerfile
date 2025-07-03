# Dockerfile for Agents Service
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements-agents.txt .
RUN pip install --no-cache-dir -r requirements-agents.txt

# Copy the agents source code
COPY ../../agents/ ./agents/
COPY ../../src/ ./src/
COPY ../../config/ ./config/

# Copy main entry point for agents service
COPY agents_main.py .

# Set environment variables
ENV PYTHONPATH=/app
ENV LOG_LEVEL=INFO

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8005/health || exit 1

# Expose port for agents service
EXPOSE 8005

# Run the agents service
CMD ["python", "agents_main.py"]
