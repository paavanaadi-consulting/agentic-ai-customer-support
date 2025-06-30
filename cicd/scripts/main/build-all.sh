#!/bin/bash
# Build all Docker services for Agentic AI Customer Support

set -e

echo "🔨 Building Agentic AI Customer Support Docker Services..."

# Change to cicd directory (we're in scripts/main subfolder)
cd "$(dirname "$0")/../.."

echo "📋 Building services in order..."

# Build services
echo "🏗️  Building PostgreSQL service..."
docker-compose build postgres

echo "🏗️  Building API service..."
docker-compose build api-service

echo "🏗️  Building Agents service..."
docker-compose build agents-service

echo "🏗️  Building MCP services..."
docker-compose build mcp-database mcp-kafka-wrapper mcp-aws

echo "🏗️  Building Main Application..."
docker-compose build main-app

echo "✅ All services built successfully!"

# Show final status
echo "📊 Service build status:"
docker images | grep -E "(agentic|customer|support)" | head -10

echo ""
echo "🚀 To start services, run: ./scripts/start.sh"
echo "📖 For more info, check: cicd/README-Infrastructure.md"
