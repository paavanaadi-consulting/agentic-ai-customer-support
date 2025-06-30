#!/bin/bash
# Main deployment script - delegates to CI/CD scripts

CICD_DIR="./cicd"

case "$1" in
    "build")
        echo "🔨 Building the system..."
        $CICD_DIR/build.sh
        ;;
    "start")
        echo "🚀 Starting the system..."
        $CICD_DIR/start.sh
        ;;
    "stop")
        echo "🛑 Stopping the system..."
        $CICD_DIR/stop.sh
        ;;
    "restart")
        echo "🔄 Restarting the system..."
        $CICD_DIR/stop.sh
        sleep 5
        $CICD_DIR/start.sh
        ;;
    "cleanup")
        echo "🧹 Cleaning up the system..."
        $CICD_DIR/cleanup.sh
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
        $CICD_DIR/build-api.sh
        ;;
    "api-start")
        echo "🚀 Starting API component..."
        $CICD_DIR/start-api.sh
        ;;
    "api-stop")
        echo "🛑 Stopping API component..."
        $CICD_DIR/stop-api.sh
        ;;
    "api-cleanup")
        echo "🧹 Cleaning up API component..."
        $CICD_DIR/cleanup-api.sh
        ;;
    "api-logs")
        echo "📋 Showing API logs..."
        docker-compose -f $CICD_DIR/docker-compose.api.yml logs -f
        ;;
    "api-status")
        echo "📊 Checking API status..."
        docker-compose -f $CICD_DIR/docker-compose.api.yml ps
        ;;
    *)
        echo "🐳 Agentic AI Customer Support - Docker Management"
        echo ""
        echo "Usage: $0 {build|start|stop|restart|cleanup|logs|status|api-build|api-start|api-stop|api-cleanup|api-logs|api-status}"
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
        echo ""
        echo "Examples:"
        echo "  $0 build && $0 start                    # Full system"
        echo "  $0 api-build && $0 api-start           # API only"
        echo "  $0 api-logs                            # API logs"
        echo "  $0 status                              # All services"
        exit 1
        ;;
esac
