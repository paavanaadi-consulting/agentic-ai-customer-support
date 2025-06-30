#!/bin/bash
# View logs for Docker services

set -e

# Change to cicd directory (we're already in scripts subfolder)
cd "$(dirname "$0")/.."

echo "📋 Agentic AI Customer Support - Log Viewer"
echo ""

# If a service name is provided as argument, show logs for that service
if [ $# -eq 1 ]; then
    SERVICE_NAME=$1
    echo "📄 Showing logs for service: $SERVICE_NAME"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    docker-compose logs -f --tail=50 "$SERVICE_NAME"
else
    echo "Available services:"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    docker-compose ps --services
    echo ""
    echo "Usage examples:"
    echo "  ./scripts/logs.sh                    # Show all logs"
    echo "  ./scripts/logs.sh api-service        # Show API service logs"
    echo "  ./scripts/logs.sh agents-service     # Show Agents service logs"
    echo "  ./scripts/logs.sh postgres           # Show PostgreSQL logs"
    echo "  ./scripts/logs.sh main-app           # Show Main app logs"
    echo ""
    
    read -p "Enter service name (or press Enter for all logs): " SERVICE_NAME
    
    if [ -z "$SERVICE_NAME" ]; then
        echo "📄 Showing all service logs (last 20 lines each):"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        docker-compose logs --tail=20
    else
        echo "📄 Showing logs for service: $SERVICE_NAME"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        docker-compose logs -f --tail=50 "$SERVICE_NAME"
    fi
fi
