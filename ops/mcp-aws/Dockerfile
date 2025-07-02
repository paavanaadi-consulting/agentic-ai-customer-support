FROM python:3.9-slim

WORKDIR /app

# Install required system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    netcat-openbsd \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy scripts and configuration files
COPY entrypoint.sh .
COPY config/ ./config/
COPY health_check.sh .

# Make scripts executable
RUN chmod +x entrypoint.sh health_check.sh

# Expose ports for each MCP server
# Lambda Tool MCP Server
EXPOSE 8766
# Messaging (SNS/SQS) MCP Server
EXPOSE 8767
# MQ MCP Server
EXPOSE 8768

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV AWS_MCP_LAMBDA_PORT=8766
ENV AWS_MCP_MESSAGING_PORT=8767
ENV AWS_MCP_MQ_PORT=8768

# Set entrypoint
ENTRYPOINT ["/app/entrypoint.sh"]

# Default command - can be overridden
CMD ["all"]
