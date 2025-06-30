#!/bin/bash
# Cleanup script for API component only

set -e  # Exit on any error

echo "🧹 Cleaning up API Component..."

# Change to cicd directory (we're in scripts/main/api subfolder)
cd "$(dirname "$0")/../../.."

# Stop and remove API containers, networks, and volumes
docker-compose -f docker-compose.api.yml down -v --remove-orphans

# Remove API-specific images
echo "🗑️  Removing API Docker images..."
docker rmi $(docker images "*api-service*" -q) 2>/dev/null || true

# Clean up local data directories
echo "🗑️  Cleaning up API log files..."
rm -rf ./logs/api*.log 2>/dev/null || true

echo "✅ API cleanup completed successfully!"
echo "🚀 To start fresh, run: ./scripts/main/api/build-api.sh && ./scripts/main/api/start-api.sh"
