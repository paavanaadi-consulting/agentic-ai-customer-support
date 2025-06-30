#!/bin/bash
# Stop script for the agentic AI customer support system

set -e  # Exit on any error

echo "🛑 Stopping Agentic AI Customer Support System..."

# Change to cicd directory (we're in scripts/main subfolder)
cd "$(dirname "$0")/../.."

# Stop all services
docker-compose -f docker-compose.yml down

echo "✅ All services stopped successfully!"
echo "🧹 To clean up volumes and networks, run: ./scripts/main/cleanup.sh"
