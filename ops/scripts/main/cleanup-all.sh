#!/bin/bash
# Cleanup all Docker services and volumes for Agentic AI Customer Support

set -e

echo "🗑️  Cleaning up Agentic AI Customer Support Infrastructure..."

# Change to cicd directory (we're already in scripts subfolder)
cd "$(dirname "$0")/.."

echo "⚠️  WARNING: This will remove all containers, volumes, and data!"
echo "📊 Current service status:"
docker-compose ps

echo ""
read -p "Are you sure you want to continue? (y/N): " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Cleanup cancelled."
    exit 1
fi

echo "🛑 Stopping all services..."
docker-compose down

echo "🗑️  Removing containers, networks, and volumes..."
docker-compose down -v --remove-orphans

echo "🧹 Removing unused Docker images..."
docker image prune -f

echo "🧹 Removing unused Docker networks..."
docker network prune -f

echo "🧹 Removing unused Docker volumes..."
docker volume prune -f

echo "📊 Cleaning up project-specific volumes..."
# Remove specific volumes if they exist
VOLUMES=(
    "cicd_pgdata"
    "cicd_redisdata" 
    "agentic-ai-customer-support_pgdata"
    "agentic-ai-customer-support_redisdata"
)

for volume in "${VOLUMES[@]}"; do
    if docker volume ls -q | grep -q "^${volume}$"; then
        echo "🗑️  Removing volume: $volume"
        docker volume rm "$volume" 2>/dev/null || true
    fi
done

echo "🧹 Cleaning up logs directory..."
if [ -d "../logs" ]; then
    rm -rf ../logs/*
    echo "📝 Logs directory cleaned"
fi

echo "🧹 Cleaning up qdrant data directory..."
if [ -d "../qdrant_data" ]; then
    rm -rf ../qdrant_data/*
    echo "📊 Qdrant data directory cleaned"
fi

echo "✅ Cleanup completed!"

echo ""
echo "📊 Final Docker status:"
echo "Containers:"
docker ps -a | head -5
echo ""
echo "Images:"
docker images | grep -E "(agentic|customer|support)" | head -5 || echo "No project images found"
echo ""
echo "Volumes:"
docker volume ls | grep -E "(agentic|customer|support|pgdata|redisdata)" || echo "No project volumes found"

echo ""
echo "🚀 To rebuild and restart: ./scripts/build-all.sh && ./scripts/start-all.sh"
echo "📖 For more info, check: README-Infrastructure.md"
