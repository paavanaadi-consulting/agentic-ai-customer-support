#!/bin/bash
# AWS MCP Server Docker script

set -e

# Set working directory to ops folder (where docker-compose.yml is located)
cd "$(dirname "$0")/../../"

# Load environment variables
if [ -f .env ]; then
  export $(grep -v '^#' .env | xargs)
fi

case "$1" in
  "build")
    echo "🔨 Building AWS MCP servers..."
    docker-compose -f docker-compose.yml build mcp-aws
    ;;
  "start")
    echo "🚀 Starting AWS MCP servers..."
    docker-compose -f docker-compose.yml up -d mcp-aws
    echo "✅ AWS MCP servers started successfully"
    echo "📋 View logs with: ./scripts/main/aws-mcp.sh logs"
    ;;
  "stop")
    echo "🛑 Stopping AWS MCP servers..."
    docker-compose -f docker-compose.yml stop mcp-aws
    echo "✅ AWS MCP servers stopped successfully"
    ;;
  "restart")
    echo "🔄 Restarting AWS MCP servers..."
    docker-compose -f docker-compose.yml restart mcp-aws
    echo "✅ AWS MCP servers restarted successfully"
    ;;
  "logs")
    echo "📋 Showing AWS MCP server logs..."
    docker-compose -f docker-compose.yml logs -f mcp-aws
    ;;
  "status")
    echo "📊 Checking AWS MCP server status..."
    docker-compose -f docker-compose.yml ps mcp-aws
    ;;
  "test")
    echo "🧪 Testing AWS MCP server endpoints..."
    # Test Lambda MCP endpoint
    echo "Testing Lambda MCP server (port $MCP_AWS_LAMBDA_PORT)..."
    curl -s http://localhost:$MCP_AWS_LAMBDA_PORT/health || echo "❌ Lambda MCP server not responding"
    
    # Test Messaging MCP endpoint
    echo "Testing Messaging MCP server (port $MCP_AWS_MESSAGING_PORT)..."
    curl -s http://localhost:$MCP_AWS_MESSAGING_PORT/health || echo "❌ Messaging MCP server not responding"
    
    # Test MQ MCP endpoint
    echo "Testing MQ MCP server (port $MCP_AWS_MQ_PORT)..."
    curl -s http://localhost:$MCP_AWS_MQ_PORT/health || echo "❌ MQ MCP server not responding"
    ;;
  *)
    echo "Usage: $0 {build|start|stop|restart|logs|status|test}"
    exit 1
    ;;
esac
