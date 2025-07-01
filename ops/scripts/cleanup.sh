#!/bin/bash

# Cleanup Script for Agentic AI Customer Support Kubernetes Deployment
# This script removes all deployed resources from Kubernetes

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OPS_DIR="$(dirname "$SCRIPT_DIR")"
KUSTOMIZE_DIR="$OPS_DIR/kubernetes"

# Default values
CLOUD_PROVIDER=""
NAMESPACE="agentic-ai-support"
FORCE=false
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
Cleanup Script for Agentic AI Customer Support

Usage: $0 [OPTIONS]

OPTIONS:
    -c, --cloud PROVIDER    Cloud provider (aws|azure|gcp)
    -n, --namespace NAME    Kubernetes namespace (default: agentic-ai-support)
    -f, --force            Skip confirmation prompts
    -v, --verbose          Enable verbose output
    -h, --help             Show this help message

EXAMPLES:
    # Clean up AWS deployment
    $0 --cloud aws

    # Force cleanup without confirmation
    $0 --cloud azure --force

    # Clean up base deployment
    $0 --namespace my-app

PREREQUISITES:
    - kubectl configured with cluster access
    - kustomize (or kubectl with built-in kustomize)

For detailed documentation, see: docs/ops/README.md

EOF
}

# Confirm deletion
confirm_deletion() {
    if [ "$FORCE" = true ]; then
        return 0
    fi

    echo
    log_warning "This will delete ALL resources in namespace '$NAMESPACE'"
    log_warning "This action CANNOT be undone!"
    echo
    read -p "Are you sure you want to continue? (yes/no): " -r
    echo
    
    if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
        log_info "Cleanup cancelled by user"
        exit 0
    fi
}

# Cleanup function
cleanup() {
    local kustomize_path="$KUSTOMIZE_DIR/base"
    
    if [ -n "$CLOUD_PROVIDER" ]; then
        kustomize_path="$KUSTOMIZE_DIR/overlays/$CLOUD_PROVIDER"
        
        if [ ! -d "$kustomize_path" ]; then
            log_error "Overlay directory for $CLOUD_PROVIDER not found: $kustomize_path"
            exit 1
        fi
    fi

    log_info "Cleaning up from: $kustomize_path"

    # Check if namespace exists
    if ! kubectl get namespace "$NAMESPACE" &> /dev/null; then
        log_warning "Namespace '$NAMESPACE' does not exist. Nothing to clean up."
        exit 0
    fi

    # Show what will be deleted
    log_info "Resources to be deleted:"
    kubectl get all -n "$NAMESPACE" 2>/dev/null || log_warning "No resources found in namespace"

    confirm_deletion

    # Delete resources using kustomize
    local kubectl_cmd="kubectl"
    if [ "$VERBOSE" = true ]; then
        kubectl_cmd="$kubectl_cmd --v=6"
    fi

    log_info "Deleting Kubernetes resources..."
    
    if command -v kustomize &> /dev/null; then
        # Use standalone kustomize
        kustomize build "$kustomize_path" | $kubectl_cmd delete -f - --ignore-not-found=true
    else
        # Use kubectl built-in kustomize
        $kubectl_cmd delete -k "$kustomize_path" --ignore-not-found=true
    fi

    # Delete PVCs if they still exist
    log_info "Cleaning up persistent volume claims..."
    kubectl delete pvc --all -n "$NAMESPACE" --ignore-not-found=true

    # Delete namespace
    log_info "Deleting namespace: $NAMESPACE"
    kubectl delete namespace "$NAMESPACE" --ignore-not-found=true

    log_success "Cleanup completed successfully!"
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
        -f|--force)
            FORCE=true
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
    log_info "Starting cleanup for Agentic AI Customer Support"
    
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
    
    cleanup
    
    log_success "Cleanup script completed successfully!"
}

# Run main function
main "$@"
