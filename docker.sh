#!/bin/bash
# Main deployment script - delegates to CI/CD scripts

CICD_DIR="./ops"

case "$1" in
    "build")
        echo "🔨 Building the system..."
        $CICD_DIR/scripts/main/build.sh
        ;;
    "start")
        echo "🚀 Starting the system..."
        $CICD_DIR/scripts/main/start.sh
        ;;
    "stop")
        echo "🛑 Stopping the system..."
        $CICD_DIR/scripts/main/stop.sh
        ;;
    "restart")
        echo "🔄 Restarting the system..."
        $CICD_DIR/scripts/main/stop.sh
        sleep 5
        $CICD_DIR/scripts/main/start.sh
        ;;
    "cleanup")
        echo "🧹 Cleaning up the system..."
        $CICD_DIR/scripts/main/cleanup.sh
        ;;
    "logs")
        echo "📋 Showing logs..."
        docker-compose -f $CICD_DIR/docker-compose.yml logs -f
        ;;
    "status")
        echo "📊 Checking service status..."
        docker-compose -f $CICD_DIR/docker-compose.yml ps
        ;;
    "api-build")
        echo "🔨 Building API component..."
        $CICD_DIR/scripts/main/api/build-api.sh
        ;;
    "api-start")
        echo "🚀 Starting API component..."
        $CICD_DIR/scripts/main/api/start-api.sh
        ;;
    "api-stop")
        echo "🛑 Stopping API component..."
        $CICD_DIR/scripts/main/api/stop-api.sh
        ;;
    "api-cleanup")
        echo "🧹 Cleaning up API component..."
        $CICD_DIR/scripts/main/api/cleanup-api.sh
        ;;
    "api-logs")
        echo "📋 Showing API logs..."
        docker-compose -f $CICD_DIR/docker-compose.yml logs -f api-service
        ;;
    "api-status")
        echo "📊 Checking API status..."
        docker-compose -f $CICD_DIR/docker-compose.yml ps api-service
        ;;
    "aws-build")
        echo "🔨 Building AWS MCP component..."
        $CICD_DIR/scripts/main/aws-mcp.sh build
        ;;
    "aws-start")
        echo "🚀 Starting AWS MCP component..."
        $CICD_DIR/scripts/main/aws-mcp.sh start
        ;;
    "aws-stop")
        echo "🛑 Stopping AWS MCP component..."
        $CICD_DIR/scripts/main/aws-mcp.sh stop
        ;;
    "aws-restart")
        echo "🔄 Restarting AWS MCP component..."
        $CICD_DIR/scripts/main/aws-mcp.sh restart
        ;;
    "aws-logs")
        echo "📋 Showing AWS MCP logs..."
        $CICD_DIR/scripts/main/aws-mcp.sh logs
        ;;
    "aws-status")
        echo "📊 Checking AWS MCP status..."
        $CICD_DIR/scripts/main/aws-mcp.sh status
        ;;
    "aws-test")
        echo "🧪 Testing AWS MCP endpoints..."
        $CICD_DIR/scripts/main/aws-mcp.sh test
        ;;
    *)
        echo "🐳 Agentic AI Customer Support - Docker Management"
        echo ""
        echo "Usage: $0 {build|start|stop|restart|cleanup|logs|status|api-build|api-start|api-stop|api-cleanup|api-logs|api-status|aws-build|aws-start|aws-stop|aws-restart|aws-logs|aws-status|aws-test}"
        echo ""
        echo "Commands:"
        echo "  build         - Build all Docker images"
        echo "  start         - Start all services"
        echo "  stop          - Stop all services"
        echo "  restart       - Restart all services"
        echo "  cleanup       - Remove containers, volumes, and data"
        echo "  logs          - Show real-time logs"
        echo "  status        - Show service status"
        echo "  api-build     - Build API component"
        echo "  api-start     - Start API component"
        echo "  api-stop      - Stop API component"
        echo "  api-cleanup   - Remove API component containers, volumes, and data"
        echo "  api-logs      - Show real-time API logs"
        echo "  api-status    - Show API service status"
        echo "  aws-build     - Build AWS MCP component"
        echo "  aws-start     - Start AWS MCP component"
        echo "  aws-stop      - Stop AWS MCP component"
        echo "  aws-restart   - Restart AWS MCP component"
        echo "  aws-logs      - Show real-time AWS MCP logs"
        echo "  aws-status    - Show AWS MCP service status"
        echo "  aws-test      - Test AWS MCP endpoints"
        echo ""
        echo "Examples:"
        echo "  $0 build && $0 start                    # Full system"
        echo "  $0 api-build && $0 api-start           # API only"
        echo "  $0 aws-build && $0 aws-start           # AWS MCP only"
        echo "  $0 aws-logs                            # AWS MCP logs"
        echo "  $0 aws-test                            # Test AWS MCP endpoints"
        echo "  $0 status                              # All services"
        exit 1
        ;;
esac
