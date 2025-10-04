#!/bin/bash

# Management script for the full stack deployment
# This script provides simplified commands to manage all services

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OPS_DIR="$SCRIPT_DIR/ops"

print_usage() {
    cat << EOF
Usage: $0 [COMMAND] [OPTIONS]

Commands:
    start-all           Start all core services (postgres, qdrant, kafka, app)
    start-full          Start all services including monitoring and CI/CD
    stop-all            Stop all services
    restart-all         Restart all services
    status              Show status of all services
    logs [SERVICE]      Show logs for all services or specific service
    clean               Clean up all containers and volumes
    build               Build all Docker images
    update              Pull latest images and restart services

Core Services:
    postgres, qdrant, kafka, app

Monitoring Services:
    prometheus, grafana, jaeger

CI/CD Services:
    jenkins, sonarqube

Options:
    -d, --detach        Run in detached mode (background)
    -f, --force         Force operation (skip confirmations)
    -v, --verbose       Verbose output
    --dev               Use development configuration
    --prod              Use production configuration

Examples:
    $0 start-all -d              # Start core services in background
    $0 start-full --dev          # Start all services with dev config
    $0 logs postgres             # Show postgres logs
    $0 status                    # Show all service status
    $0 clean -f                  # Force clean all resources

EOF
}

# Default values
DETACH=""
FORCE=false
VERBOSE=false
ENVIRONMENT="dev"

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -d|--detach)
            DETACH="-d"
            shift
            ;;
        -f|--force)
            FORCE=true
            shift
            ;;
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        --dev)
            ENVIRONMENT="dev"
            shift
            ;;
        --prod)
            ENVIRONMENT="prod"
            shift
            ;;
        *)
            if [[ -z "${COMMAND:-}" ]]; then
                COMMAND="$1"
            elif [[ -z "${SERVICE:-}" ]]; then
                SERVICE="$1"
            fi
            shift
            ;;
    esac
done

# Set compose files based on environment
COMPOSE_FILES="-f $OPS_DIR/docker-compose.yml"
if [[ "$ENVIRONMENT" == "dev" ]]; then
    COMPOSE_FILES="$COMPOSE_FILES -f $OPS_DIR/docker-compose.dev.yml"
elif [[ "$ENVIRONMENT" == "prod" ]]; then
    COMPOSE_FILES="$COMPOSE_FILES -f $OPS_DIR/docker-compose.prod.yml"
fi

# Helper functions
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') [INFO] $*"
}

error() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') [ERROR] $*" >&2
}

verbose() {
    if [[ "$VERBOSE" == true ]]; then
        echo "$(date '+%Y-%m-%d %H:%M:%S') [DEBUG] $*"
    fi
}

confirm() {
    if [[ "$FORCE" == true ]]; then
        return 0
    fi
    read -p "$1 (y/N): " -n 1 -r
    echo
    [[ $REPLY =~ ^[Yy]$ ]]
}

check_dependencies() {
    verbose "Checking dependencies..."
    command -v docker >/dev/null 2>&1 || { error "Docker is required but not installed."; exit 1; }
    command -v docker-compose >/dev/null 2>&1 || { error "Docker Compose is required but not installed."; exit 1; }
}

# Core service groups
CORE_SERVICES="postgres qdrant kafka app"
MONITORING_SERVICES="prometheus grafana jaeger"
CICD_SERVICES="jenkins sonarqube"
ALL_SERVICES="$CORE_SERVICES $MONITORING_SERVICES $CICD_SERVICES"

# Command implementations
cmd_start_all() {
    log "Starting core services..."
    verbose "Services: $CORE_SERVICES"
    cd "$OPS_DIR"
    docker-compose $COMPOSE_FILES up $DETACH $CORE_SERVICES
}

cmd_start_full() {
    log "Starting all services including monitoring and CI/CD..."
    verbose "Services: $ALL_SERVICES"
    cd "$OPS_DIR"
    docker-compose $COMPOSE_FILES up $DETACH
}

cmd_stop_all() {
    log "Stopping all services..."
    cd "$OPS_DIR"
    docker-compose $COMPOSE_FILES down
}

cmd_restart_all() {
    log "Restarting all services..."
    cmd_stop_all
    sleep 2
    cmd_start_all
}

cmd_status() {
    log "Checking service status..."
    cd "$OPS_DIR"
    docker-compose $COMPOSE_FILES ps
    echo
    echo "Container health status:"
    docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
}

cmd_logs() {
    cd "$OPS_DIR"
    if [[ -n "${SERVICE:-}" ]]; then
        log "Showing logs for service: $SERVICE"
        docker-compose $COMPOSE_FILES logs -f "$SERVICE"
    else
        log "Showing logs for all services"
        docker-compose $COMPOSE_FILES logs -f
    fi
}

cmd_clean() {
    if confirm "This will remove all containers, networks, and volumes. Continue?"; then
        log "Cleaning up all resources..."
        cd "$OPS_DIR"
        docker-compose $COMPOSE_FILES down -v --remove-orphans
        docker system prune -f
        log "Cleanup completed"
    else
        log "Cleanup cancelled"
    fi
}

cmd_build() {
    log "Building all Docker images..."
    cd "$OPS_DIR"
    docker-compose $COMPOSE_FILES build
}

cmd_update() {
    log "Updating services..."
    cd "$OPS_DIR"
    docker-compose $COMPOSE_FILES pull
    docker-compose $COMPOSE_FILES up $DETACH --remove-orphans
}

# Main execution
main() {
    check_dependencies
    
    case "${COMMAND:-}" in
        start-all)
            cmd_start_all
            ;;
        start-full)
            cmd_start_full
            ;;
        stop-all)
            cmd_stop_all
            ;;
        restart-all)
            cmd_restart_all
            ;;
        status)
            cmd_status
            ;;
        logs)
            cmd_logs
            ;;
        clean)
            cmd_clean
            ;;
        build)
            cmd_build
            ;;
        update)
            cmd_update
            ;;
        help|--help|-h)
            print_usage
            ;;
        "")
            error "No command specified"
            print_usage
            exit 1
            ;;
        *)
            error "Unknown command: $COMMAND"
            print_usage
            exit 1
            ;;
    esac
}

main "$@"
