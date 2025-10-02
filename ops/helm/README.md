# Agentic AI Customer Support - Helm Chart

This Helm chart deploys the Agentic AI Customer Support application on Kubernetes, providing a complete AI-powered customer support platform with multi-agent processing capabilities.

## 🚀 **Quick Start**

### Prerequisites

- Kubernetes 1.19+
- Helm 3.x
- PV provisioner support in the underlying infrastructure

### Installation

```bash
# Add Bitnami repository for dependencies
helm repo add bitnami https://charts.bitnami.com/bitnami
helm repo update

# Install with default values
helm install agentic-ai ./ops/helm

# Install with AWS-specific configuration
helm install agentic-ai ./ops/helm -f ./ops/helm/values-aws.yaml

# Install with custom values
helm install agentic-ai ./ops/helm --set api.replicaCount=5 --set postgresql.auth.password=mypassword
```

### Using the Deployment Script

```bash
# Deploy development environment locally
./ops/helm/deploy-helm.sh

# Deploy production environment on AWS
./ops/helm/deploy-helm.sh production aws

# Deploy with auto-confirmation
./ops/helm/deploy-helm.sh staging azure --auto
```

## 📊 **Architecture Overview**

The Helm chart deploys the following components:

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   API Server    │    │  MCP Postgres   │    │   MCP Kafka     │
│   (FastAPI)     │    │    Server       │    │    Server       │
│                 │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                        │                        │
         └────────────────────────┼────────────────────────┘
                                  │
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Consumer      │    │   PostgreSQL    │    │     Kafka       │
│   Service       │    │   Database      │    │   (Bitnami)     │
│                 │    │   (Bitnami)     │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                        │                        │
         └────────────────────────┼────────────────────────┘
                                  │
                     ┌─────────────────┐
                     │     Qdrant      │
                     │  Vector Store   │
                     │                 │
                     └─────────────────┘
```

## 🔧 **Configuration**

### Core Services

| Service | Purpose | Port | Replicas |
|---------|---------|------|----------|
| **API Server** | Main FastAPI application | 8000 | 3 (configurable) |
| **MCP Postgres** | Model Context Protocol for DB | 8001 | 1 |
| **MCP Kafka** | Model Context Protocol for events | 8002 | 1 |
| **Consumer** | Event processing service | 8003 | 2 (configurable) |
| **PostgreSQL** | Primary database | 5432 | 1 |
| **Kafka** | Event streaming | 9092 | 3 |
| **Qdrant** | Vector database | 6333 | 1 |

### Multi-Cloud Support

The chart includes optimized configurations for major cloud providers:

#### AWS (EKS)
```yaml
# values-aws.yaml
cloudProvider:
  aws:
    enabled: true
global:
  storageClass: "gp3"
ingress:
  className: "alb"
  annotations:
    alb.ingress.kubernetes.io/scheme: internet-facing
    alb.ingress.kubernetes.io/target-type: ip
```

#### Azure (AKS)
```yaml
# values-azure.yaml
cloudProvider:
  azure:
    enabled: true
global:
  storageClass: "managed-premium"
ingress:
  className: "azure-application-gateway"
```

#### GCP (GKE)
```yaml
# values-gcp.yaml
cloudProvider:
  gcp:
    enabled: true
global:
  storageClass: "ssd"
ingress:
  className: "gce"
```

## 📝 **Values Configuration**

### API Configuration

```yaml
api:
  replicaCount: 3
  image:
    repository: agentic-ai/api
    tag: "latest"
    pullPolicy: IfNotPresent
  service:
    type: ClusterIP
    port: 8000
  autoscaling:
    enabled: true
    minReplicas: 2
    maxReplicas: 10
    targetCPUUtilizationPercentage: 70
  resources:
    limits:
      cpu: 1000m
      memory: 1Gi
    requests:
      cpu: 250m
      memory: 256Mi
```

### Database Configuration

```yaml
postgresql:
  enabled: true
  auth:
    postgresPassword: "change-me"
    username: "agenticai"
    password: "change-me"
    database: "customer_support"
  primary:
    persistence:
      enabled: true
      size: 20Gi
```

### Ingress Configuration

```yaml
ingress:
  enabled: true
  className: "nginx"
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
    cert-manager.io/cluster-issuer: letsencrypt-prod
  hosts:
    - host: api.agentic-ai-support.com
      paths:
        - path: /
          pathType: Prefix
          service: api
        - path: /mcp/postgres
          pathType: Prefix
          service: mcp-postgres
  tls:
    - secretName: agentic-ai-tls-secret
      hosts:
        - api.agentic-ai-support.com
```

## 🔐 **Security Configuration**

### Secrets Management

```yaml
secrets:
  claudeApiKey: ""     # Anthropic Claude API key
  openaiApiKey: ""     # OpenAI API key
  geminiApiKey: ""     # Google Gemini API key
  jwtSecret: ""        # JWT signing secret (auto-generated if empty)
```

**⚠️ Production Note**: Use external secret management systems like:
- AWS Secrets Manager
- Azure Key Vault
- GCP Secret Manager
- Kubernetes External Secrets Operator

### Network Policies

Network policies are enabled by default to secure pod-to-pod communication:

```yaml
networkPolicy:
  enabled: true  # Restricts traffic between pods
```

### Security Context

```yaml
securityContext:
  runAsNonRoot: true
  runAsUser: 1000
  fsGroup: 2000
```

## 📊 **Monitoring & Observability**

### Health Checks

All services include comprehensive health checks:

```yaml
livenessProbe:
  httpGet:
    path: /health
    port: http
  initialDelaySeconds: 30
  periodSeconds: 10

readinessProbe:
  httpGet:
    path: /health
    port: http
  initialDelaySeconds: 5
  periodSeconds: 5
```

### Autoscaling

Horizontal Pod Autoscaling is configured for API and Consumer services:

```yaml
autoscaling:
  enabled: true
  minReplicas: 2
  maxReplicas: 10
  targetCPUUtilizationPercentage: 70
```

### Pod Disruption Budgets

High availability is ensured with Pod Disruption Budgets:

```yaml
podDisruptionBudget:
  enabled: true
  minAvailable: 1
```

## 🧪 **Testing**

### Validate Chart

```bash
# Run comprehensive tests
./ops/helm/test-helm.sh

# Run specific tests
./ops/helm/test-helm.sh lint
./ops/helm/test-helm.sh structure
./ops/helm/test-helm.sh render
```

### Manual Validation

```bash
# Lint the chart
helm lint ./ops/helm

# Dry-run installation
helm install --dry-run --debug agentic-ai ./ops/helm

# Template rendering
helm template agentic-ai ./ops/helm -f ./ops/helm/values-aws.yaml
```

## 🚀 **Deployment Examples**

### Development Environment

```bash
# Local development with minimal resources
helm install agentic-ai-dev ./ops/helm \
  --set api.replicaCount=1 \
  --set consumer.replicaCount=1 \
  --set postgresql.primary.persistence.size=5Gi \
  --set kafka.replicaCount=1
```

### Staging Environment

```bash
# Staging with production-like configuration
helm install agentic-ai-staging ./ops/helm \
  -f ./ops/helm/values-aws.yaml \
  --set ingress.hosts[0].host=staging-api.agentic-ai-support.com
```

### Production Environment

```bash
# Production deployment with high availability
helm install agentic-ai-prod ./ops/helm \
  -f ./ops/helm/values-aws.yaml \
  --set api.replicaCount=5 \
  --set consumer.replicaCount=3 \
  --set postgresql.primary.persistence.size=100Gi \
  --set kafka.persistence.size=200Gi \
  --set secrets.claudeApiKey="your-claude-api-key" \
  --set secrets.openaiApiKey="your-openai-api-key" \
  --set secrets.geminiApiKey="your-gemini-api-key"
```

## 🔄 **Upgrades & Rollbacks**

### Upgrading

```bash
# Upgrade with new values
helm upgrade agentic-ai ./ops/helm -f ./ops/helm/values-aws.yaml

# Upgrade with new image tag
helm upgrade agentic-ai ./ops/helm --set api.image.tag=v2.0.0
```

### Rollback

```bash
# View release history
helm history agentic-ai

# Rollback to previous version
helm rollback agentic-ai 1
```

## 🗑️ **Cleanup**

### Uninstall Release

```bash
# Remove the Helm release
helm uninstall agentic-ai

# Remove persistent volumes (if needed)
kubectl delete pvc --all -l app.kubernetes.io/instance=agentic-ai

# Remove namespace
kubectl delete namespace agentic-ai
```

## 🛠️ **Troubleshooting**

### Common Issues

#### 1. Pending Pods

```bash
# Check pod status
kubectl get pods -l app.kubernetes.io/instance=agentic-ai

# Describe pending pods
kubectl describe pod <pod-name>

# Check node resources
kubectl top nodes
```

#### 2. Service Connection Issues

```bash
# Test service connectivity
kubectl run debug --image=busybox --rm -it -- /bin/sh
# Inside the pod:
# nslookup agentic-ai-api
# wget -O- http://agentic-ai-api:8000/health
```

#### 3. Ingress Issues

```bash
# Check ingress status
kubectl get ingress
kubectl describe ingress agentic-ai

# Check ingress controller logs
kubectl logs -n ingress-nginx deployment/ingress-nginx-controller
```

### Debug Commands

```bash
# Get all resources
kubectl get all -l app.kubernetes.io/instance=agentic-ai

# Check logs
kubectl logs -l app.kubernetes.io/name=agentic-ai-customer-support

# Port forward for local access
kubectl port-forward svc/agentic-ai-api 8000:8000

# Execute into pod
kubectl exec -it deployment/agentic-ai-api -- /bin/bash
```

## 📚 **Additional Resources**

- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [Helm Documentation](https://helm.sh/docs/)
- [Bitnami Charts](https://github.com/bitnami/charts)
- [Application Architecture Documentation](../../docs/ops/README.md)

## 🤝 **Contributing**

1. Test your changes with `./ops/helm/test-helm.sh`
2. Validate chart structure and syntax
3. Test deployment on development environment
4. Update documentation if needed
5. Submit pull request with detailed description

## 📄 **License**

This Helm chart is part of the Agentic AI Customer Support project and follows the same licensing terms.
