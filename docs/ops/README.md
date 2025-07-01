# Kubernetes Deployment for Agentic AI Customer Support

This directory contains comprehensive Kubernetes deployment configurations for the Agentic AI Customer Support application, supporting deployment across AWS, Azure, and GCP.

## 📁 Directory Structure

```
ops/
├── kubernetes/                 # Kubernetes manifests
│   ├── base/                  # Base manifests (cloud-agnostic)
│   └── overlays/              # Cloud-specific overlays
│       ├── aws/               # AWS-specific configurations
│       ├── azure/             # Azure-specific configurations
│       └── gcp/               # GCP-specific configurations
├── helm/                      # Helm charts
│   ├── templates/             # Helm templates
│   ├── values.yaml           # Default values
│   ├── values-aws.yaml       # AWS-specific values
│   ├── values-azure.yaml     # Azure-specific values
│   └── values-gcp.yaml       # GCP-specific values
├── terraform/                 # Infrastructure as Code (planned)
│   ├── aws/                  # AWS Terraform modules
│   ├── azure/                # Azure Terraform modules
│   └── gcp/                  # GCP Terraform modules
└── scripts/                  # Deployment and utility scripts
    ├── deploy.sh             # Main deployment script
    └── cleanup.sh            # Cleanup script
```

## 🚀 Quick Start

### Prerequisites

- **kubectl** configured with cluster access
- **kustomize** (or kubectl >= 1.14 with built-in kustomize)
- **helm** (for Helm deployments)
- Cloud-specific CLI tools (aws, az, gcloud)

### Option 1: Using Deployment Scripts (Recommended)

```bash
# Deploy to AWS
./ops/scripts/deploy.sh --cloud aws

# Deploy to Azure
./ops/scripts/deploy.sh --cloud azure

# Deploy to GCP
./ops/scripts/deploy.sh --cloud gcp

# Deploy base configuration (cloud-agnostic)
./ops/scripts/deploy.sh
```

### Option 2: Using Kustomize Directly

```bash
# Deploy base configuration
kubectl apply -k ops/kubernetes/base

# Deploy with AWS overlay
kubectl apply -k ops/kubernetes/overlays/aws

# Deploy with Azure overlay
kubectl apply -k ops/kubernetes/overlays/azure

# Deploy with GCP overlay
kubectl apply -k ops/kubernetes/overlays/gcp
```

### Option 3: Using Helm

```bash
# Install with default values
helm install agentic-ai ops/helm

# Install with AWS-specific values
helm install agentic-ai ops/helm -f ops/helm/values-aws.yaml

# Install with Azure-specific values
helm install agentic-ai ops/helm -f ops/helm/values-azure.yaml

# Install with GCP-specific values
helm install agentic-ai ops/helm -f ops/helm/values-gcp.yaml
```

## 🏗️ Architecture

The deployment includes the following components:

### Core Services
- **API Server** - Main application API (port 8000)
- **MCP Postgres Server** - Model Context Protocol for Postgres (port 8001)
- **MCP Kafka Server** - Model Context Protocol for Kafka (port 8002)
- **Consumer Service** - Message consumer service (port 8003)

### Dependencies
- **PostgreSQL** - Primary database
- **Apache Kafka** - Message broker with Zookeeper
- **Qdrant** - Vector database for embeddings

### Infrastructure
- **Ingress Controller** - Traffic routing and SSL termination
- **Persistent Storage** - For database and message persistence
- **Auto-scaling** - Horizontal Pod Autoscaler (HPA)
- **Network Policies** - Security and traffic control
- **Pod Disruption Budgets** - High availability

## ☁️ Cloud Provider Configurations

### AWS (EKS)

**Features:**
- Application Load Balancer (ALB) ingress
- EBS GP3 storage classes
- Network Load Balancer (NLB) for services
- IAM roles for service accounts (IRSA)
- Multi-AZ deployment

**Prerequisites:**
- EKS cluster with ALB Controller
- EBS CSI Driver
- Certificate Manager

```bash
# Deploy to AWS
kubectl apply -k ops/kubernetes/overlays/aws
```

### Azure (AKS)

**Features:**
- Application Gateway ingress
- Azure Disk Premium storage
- Azure Load Balancer
- Workload Identity
- Availability zone spread

**Prerequisites:**
- AKS cluster with Application Gateway
- Azure Disk CSI Driver
- cert-manager

```bash
# Deploy to Azure
kubectl apply -k ops/kubernetes/overlays/azure
```

### Google Cloud (GKE)

**Features:**
- Google Cloud Load Balancer
- Persistent Disk SSD storage
- Workload Identity
- Regional persistent disks
- GKE Autopilot compatibility

**Prerequisites:**
- GKE cluster with GCE ingress
- Persistent Disk CSI Driver
- Google-managed SSL certificates

```bash
# Deploy to GCP
kubectl apply -k ops/kubernetes/overlays/gcp
```

## 🔧 Configuration

### Environment Variables

Key configuration is managed through ConfigMaps and Secrets:

```yaml
# ConfigMap (ops/kubernetes/base/configmap.yaml)
POSTGRES_DB: customer_support
KAFKA_TOPICS: events,notifications
LOG_LEVEL: INFO

# Secrets (ops/kubernetes/base/secrets.yaml)
POSTGRES_USER: <base64-encoded>
POSTGRES_PASSWORD: <base64-encoded>
API_SECRET_KEY: <base64-encoded>
```

### Customization

1. **Base Configuration**: Modify files in `ops/kubernetes/base/`
2. **Cloud-Specific**: Update overlays in `ops/kubernetes/overlays/{cloud}/`
3. **Helm Values**: Customize `ops/helm/values-{cloud}.yaml`

### Scaling

```bash
# Scale API deployment
kubectl scale deployment api-deployment --replicas=5 -n agentic-ai-support

# Scale consumer deployment
kubectl scale deployment consumer-deployment --replicas=3 -n agentic-ai-support
```

## 🔍 Monitoring and Debugging

### Check Deployment Status

```bash
# Check pods
kubectl get pods -n agentic-ai-support

# Check services
kubectl get services -n agentic-ai-support

# Check ingress
kubectl get ingress -n agentic-ai-support

# Check persistent volumes
kubectl get pv,pvc -n agentic-ai-support
```

### View Logs

```bash
# API logs
kubectl logs -f deployment/api-deployment -n agentic-ai-support

# Consumer logs
kubectl logs -f deployment/consumer-deployment -n agentic-ai-support

# Postgres logs
kubectl logs -f deployment/postgres -n agentic-ai-support
```

### Troubleshooting

```bash
# Describe problematic pods
kubectl describe pod <pod-name> -n agentic-ai-support

# Check events
kubectl get events -n agentic-ai-support --sort-by=.metadata.creationTimestamp

# Test connectivity
kubectl exec -it deployment/api-deployment -n agentic-ai-support -- curl http://postgres-service:5432
```

## 🧹 Cleanup

### Using Scripts
```bash
# Clean up AWS deployment
./ops/scripts/cleanup.sh --cloud aws

# Clean up with force (no confirmation)
./ops/scripts/cleanup.sh --cloud azure --force
```

### Manual Cleanup
```bash
# Delete specific cloud deployment
kubectl delete -k ops/kubernetes/overlays/aws

# Delete base deployment
kubectl delete -k ops/kubernetes/base

# Delete namespace and all resources
kubectl delete namespace agentic-ai-support
```

### Helm Cleanup
```bash
# Uninstall Helm release
helm uninstall agentic-ai

# Delete persistent volumes (if needed)
kubectl delete pvc --all -n agentic-ai-support
```

## 🔐 Security Considerations

1. **Secrets Management**: Use external secret managers (AWS Secrets Manager, Azure Key Vault, GCP Secret Manager)
2. **Network Policies**: Enable network policies for pod-to-pod communication control
3. **RBAC**: Implement proper Role-Based Access Control
4. **Image Security**: Use signed container images and vulnerability scanning
5. **TLS**: Enable TLS for all communication (ingress, inter-service)

## 📊 Resource Requirements

### Minimum Requirements
- **CPU**: 4 cores total
- **Memory**: 8GB total
- **Storage**: 100GB total

### Production Requirements
- **CPU**: 12+ cores
- **Memory**: 24GB+
- **Storage**: 500GB+
- **Nodes**: 3+ for high availability

## 🔄 CI/CD Integration

The deployment structure supports integration with various CI/CD systems:

```yaml
# Example GitHub Actions workflow
- name: Deploy to Kubernetes
  run: |
    ./ops/scripts/deploy.sh --cloud aws --namespace production
```

## 📖 Additional Resources

- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [Kustomize Documentation](https://kustomize.io/)
- [Helm Documentation](https://helm.sh/docs/)
- [AWS EKS Best Practices](https://aws.github.io/aws-eks-best-practices/)
- [Azure AKS Best Practices](https://docs.microsoft.com/en-us/azure/aks/)
- [GKE Best Practices](https://cloud.google.com/kubernetes-engine/docs/best-practices)

## 🆘 Support

For issues and questions:
1. Check the troubleshooting section above
2. Review pod logs and events
3. Consult cloud provider documentation
4. Open an issue in the repository

---

**Note**: Before deploying to production, ensure you:
1. Update all placeholder values (passwords, domains, etc.)
2. Configure proper backup strategies
3. Set up monitoring and alerting
4. Review security settings
5. Test disaster recovery procedures
