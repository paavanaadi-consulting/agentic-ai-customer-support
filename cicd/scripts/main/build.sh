#!/bin/bash
# Build script for the agentic AI customer support system

set -e  # Exit on any error

echo "🐳 Building Agentic AI Customer Support System..."

# Change to cicd directory (we're in scripts/main subfolder)
cd "$(dirname "$0")/../.."

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker Desktop and try again."
    exit 1
fi

# Build all services
echo "🔨 Building all Docker services..."
docker-compose -f docker-compose.yml build --parallel

echo "✅ Build completed successfully!"
echo "🚀 To start the services, run: ./scripts/main/start.sh"
