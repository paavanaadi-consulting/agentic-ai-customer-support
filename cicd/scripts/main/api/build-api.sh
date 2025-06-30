#!/bin/bash
# Build script for API component only

set -e  # Exit on any error

echo "🔨 Building API Component..."

# Change to cicd directory (we're in scripts/main/api subfolder)
cd "$(dirname "$0")/../../.."

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker Desktop and try again."
    exit 1
fi

# Build API service
echo "🔨 Building API Docker image..."
docker-compose build api-service

echo "✅ API build completed successfully!"
echo "🚀 To start the API service, run: ./scripts/main/api/start-api.sh"
echo "🏥 To test the API, run: ./scripts/test/test-api.sh"
