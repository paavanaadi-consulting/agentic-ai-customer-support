# Dockerfile for the main application (agentic-ai-customer-support service)
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app

# Install git client, which is required for installing packages from git repositories
RUN apt-get update && apt-get install -y --no-install-recommends git && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies first to leverage Docker layer caching
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Expose the port the app runs on
EXPOSE 8000

# The command to run the application will be taken from docker-compose.yml, but this is a good default.
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]