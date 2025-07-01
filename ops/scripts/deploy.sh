#!/bin/bash

# Kubernetes Deployment Script for Agentic AI Customer Support
# This script deploys the application to Kubernetes with cloud-specific configurations

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OPS_DIR="$(dirname "$SCRIPT_DIR")"
KUSTOMIZE_DIR="$OPS_DIR/kubernetes"

# Default values
CLOUD_PROVIDER=""
NAMESPACE="agentic-ai-support"
DRY_RUN=false
VERBOSE=false

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Help function
show_help() {
    cat << EOF
Kubernetes Deployment Script for Agentic AI Customer Support

Usage: $0 [OPTIONS]

OPTIONS:
    -c, --cloud PROVIDER    Cloud provider (aws|azure|gcp)
    -n, --namespace NAME    Kubernetes namespace (default: agentic-ai-support)
    -d, --dry-run          Show what would be deployed without applying
    -v, --verbose          Enable verbose output
    -h, --help             Show this help message

EXAMPLES:
    # Deploy to AWS
    $0 --cloud aws

    # Deploy to Azure with custom namespace
    $0 --cloud azure --namespace my-app

    # Dry run for GCP
    $0 --cloud gcp --dry-run

    # Deploy base configuration (cloud-agnostic)
    $0

PREREQUISITES:
    - kubectl configured with cluster access
    - kustomize (or kubectl with built-in kustomize)
    - Appropriate cloud provider CLI tools (aws, az, gcloud)

For detailed documentation, see: docs/ops/README.md

EOF
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."

    # Check kubectl
    if ! command -v kubectl &> /dev/null; then
        log_error "kubectl is not installed or not in PATH"
        exit 1
    fi

    # Check if kubectl can connect to cluster
    if ! kubectl cluster-info &> /dev/null; then
        log_error "Cannot connect to Kubernetes cluster. Please check your kubeconfig."
        exit 1
    fi

    # Check kustomize (either standalone or kubectl built-in)
    if ! (command -v kustomize &> /dev/null || kubectl kustomize --help &> /dev/null); then
        log_error "kustomize is not available. Please install kustomize or use kubectl >= 1.14"
        exit 1
    fi

    log_success "Prerequisites check passed"
}

# Validate cloud provider
validate_cloud_provider() {
    if [ -n "$CLOUD_PROVIDER" ]; then
        case "$CLOUD_PROVIDER" in
            aws|azure|gcp)
                log_info "Using cloud provider: $CLOUD_PROVIDER"
                ;;
            *)
                log_error "Invalid cloud provider: $CLOUD_PROVIDER. Valid options: aws, azure, gcp"
                exit 1
                ;;
        esac
    else
        log_info "No cloud provider specified. Using base configuration."
    fi
}

# Deploy to Kubernetes
deploy() {
    local kustomize_path="$KUSTOMIZE_DIR/base"
    
    if [ -n "$CLOUD_PROVIDER" ]; then
        kustomize_path="$KUSTOMIZE_DIR/overlays/$CLOUD_PROVIDER"
        
        if [ ! -d "$kustomize_path" ]; then
            log_error "Overlay directory for $CLOUD_PROVIDER not found: $kustomize_path"
            exit 1
        fi
    fi

    log_info "Deploying from: $kustomize_path"

    # Create namespace if it doesn't exist
    if ! kubectl get namespace "$NAMESPACE" &> /dev/null; then
        log_info "Creating namespace: $NAMESPACE"
        if [ "$DRY_RUN" = false ]; then
            kubectl create namespace "$NAMESPACE"
        else
            log_info "[DRY-RUN] Would create namespace: $NAMESPACE"
        fi
    fi

    # Build and apply manifests
    local kubectl_cmd="kubectl"
    if [ "$DRY_RUN" = true ]; then
        kubectl_cmd="kubectl --dry-run=client"
    fi

    if [ "$VERBOSE" = true ]; then
        kubectl_cmd="$kubectl_cmd --v=6"
    fi

    log_info "Building and applying Kubernetes manifests..."
    
    if command -v kustomize &> /dev/null; then
        # Use standalone kustomize
        if [ "$DRY_RUN" = true ]; then
            kustomize build "$kustomize_path"
        else
            kustomize build "$kustomize_path" | $kubectl_cmd apply -f -
        fi
    else
        # Use kubectl built-in kustomize
        $kubectl_cmd apply -k "$kustomize_path"
    fi

    if [ "$DRY_RUN" = false ]; then
        log_success "Deployment completed successfully!"
        
        # Show deployment status
        log_info "Checking deployment status..."
        kubectl get pods -n "$NAMESPACE"
        kubectl get services -n "$NAMESPACE"
        
        # Wait for deployments to be ready
        log_info "Waiting for deployments to be ready..."
        kubectl rollout status deployment/api-deployment -n "$NAMESPACE" --timeout=300s
        kubectl rollout status deployment/postgres -n "$NAMESPACE" --timeout=300s
        
        log_success "All deployments are ready!"
    else
        log_info "Dry run completed. No changes were applied."
    fi
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -c|--cloud)
            CLOUD_PROVIDER="$2"
            shift 2
            ;;
        -n|--namespace)
            NAMESPACE="$2"
            shift 2
            ;;
        -d|--dry-run)
            DRY_RUN=true
            shift
            ;;
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        *)
            log_error "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

# Main execution
main() {
    log_info "Starting Kubernetes deployment for Agentic AI Customer Support"
    
    check_prerequisites
    validate_cloud_provider
    deploy
    
    log_success "Script completed successfully!"
}

# Run main function
main "$@"
