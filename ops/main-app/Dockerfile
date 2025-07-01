# Dockerfile for the main application (agentic-ai-customer-support service)
# Using Jupyter scipy-notebook as base image with pre-installed scientific packages
FROM jupyter/scipy-notebook:latest

# Switch to root to install system dependencies
USER root

# Install minimal system dependencies 
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    && rm -rf /var/lib/apt/lists/*

# Switch back to the default user
USER $NB_UID

# Set the working directory
WORKDIR /app

# Copy optimized requirements for Docker (excludes heavy packages)
COPY ops/requirements-docker.txt ./requirements-docker.txt

# Install remaining dependencies
RUN pip install --no-cache-dir -r requirements-docker.txt

# Copy the rest of the application code
COPY . .

# Expose the port the app runs on
EXPOSE 8000

# The command to run the application will be taken from docker-compose.yml, but this is a good default.
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
