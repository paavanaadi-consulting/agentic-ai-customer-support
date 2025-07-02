#!/bin/bash
# Cleanup script for the agentic AI customer support system

set -e  # Exit on any error

echo "🧹 Cleaning up Agentic AI Customer Support System..."

# Stop and remove all containers, networks, and volumes
docker-compose -f ops/docker-compose.yml down -v --remove-orphans

# Remove unused Docker resources
echo "🗑️  Removing unused Docker resources..."
docker system prune -f

# Remove specific volumes if they exist
echo "🗑️  Removing application volumes..."
docker volume rm -f agentic-ai-customer-support_pgdata 2>/dev/null || true
docker volume rm -f agentic-ai-customer-support_redisdata 2>/dev/null || true

# Clean up local data directories
echo "🗑️  Cleaning up local data directories..."
rm -rf ./qdrant_data 2>/dev/null || true
rm -rf ./logs/*.log 2>/dev/null || true

echo "✅ Cleanup completed successfully!"
echo "🚀 To start fresh, run: ./ops/build.sh && ./ops/start.sh"
