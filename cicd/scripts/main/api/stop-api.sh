#!/bin/bash
# Stop script for API component only

set -e  # Exit on any error

echo "🛑 Stopping API Component..."

# Change to cicd directory (we're in scripts/main/api subfolder)
cd "$(dirname "$0")/../../.."

# Stop API services
docker-compose -f docker-compose.yml stop api-service

echo "✅ API services stopped successfully!"
echo "🧹 To clean up API volumes, run: ./scripts/main/api/cleanup-api.sh"
