# Helm Chart Documentation

## Overview

The Agentic AI Customer Support Helm chart provides a complete Kubernetes deployment package for the entire microservices stack, including AI agents, MCP (Model Context Protocol) servers, databases, and event streaming infrastructure.

## Chart Structure

```
ops/helm/
├── Chart.yaml                 # Chart metadata and dependencies
├── values.yaml                # Default configuration values
├── values-aws.yaml            # AWS-specific configurations
├── values-azure.yaml          # Azure-specific configurations
├── values-gcp.yaml            # GCP-specific configurations
└── templates/
    └── _helpers.tpl           # Template helper functions
```

## Prerequisites

- Kubernetes 1.20+
- Helm 3.0+
- Ingress Controller (nginx, ALB, or Application Gateway)
- Cert-manager (for SSL certificates)
- Persistent Volume Provisioner

## Installation

### Quick Start

```bash
# Add required repositories
helm repo add bitnami https://charts.bitnami.com/bitnami
helm repo update

# Install with default values
helm install agentic-ai-support ops/helm/

# Install with cloud-specific values
helm install agentic-ai-support ops/helm/ -f ops/helm/values-aws.yaml
```

### Production Installation

```bash
# Create namespace
kubectl create namespace agentic-ai

# Install with custom values
helm install agentic-ai-support ops/helm/ \
  --namespace agentic-ai \
  --set postgresql.auth.postgresPassword="your-secure-password" \
  --set postgresql.auth.password="your-app-password" \
  --set ingress.hosts[0].host="your-domain.com" \
  -f ops/helm/values-aws.yaml
```

## Configuration

### Global Settings

| Parameter | Description | Default |
|-----------|-------------|---------|
| `global.imageRegistry` | Global Docker registry | `""` |
| `global.imagePullSecrets` | Global image pull secrets | `[]` |
| `global.storageClass` | Global storage class | `""` |

### Application Configuration

| Parameter | Description | Default |
|-----------|-------------|---------|
| `app.name` | Application name | `agentic-ai-customer-support` |
| `app.version` | Application version | `1.0.0` |

### API Service Configuration

| Parameter | Description | Default |
|-----------|-------------|---------|
| `api.replicaCount` | Number of API replicas | `3` |
| `api.image.repository` | API image repository | `agentic-ai/api` |
| `api.image.tag` | API image tag | `latest` |
| `api.service.port` | API service port | `8000` |
| `api.resources.limits.cpu` | CPU limit | `1000m` |
| `api.resources.limits.memory` | Memory limit | `1Gi` |
| `api.autoscaling.enabled` | Enable HPA | `true` |
| `api.autoscaling.minReplicas` | Minimum replicas | `2` |
| `api.autoscaling.maxReplicas` | Maximum replicas | `10` |
| `api.autoscaling.targetCPUUtilizationPercentage` | CPU target | `70` |

### MCP Services Configuration

#### PostgreSQL MCP Server

| Parameter | Description | Default |
|-----------|-------------|---------|
| `mcpPostgres.enabled` | Enable PostgreSQL MCP server | `true` |
| `mcpPostgres.replicaCount` | Number of replicas | `1` |
| `mcpPostgres.image.repository` | Image repository | `agentic-ai/mcp-postgres` |
| `mcpPostgres.service.port` | Service port | `8001` |
| `mcpPostgres.resources.limits.cpu` | CPU limit | `500m` |
| `mcpPostgres.resources.limits.memory` | Memory limit | `512Mi` |

#### Kafka MCP Server

| Parameter | Description | Default |
|-----------|-------------|---------|
| `mcpKafka.enabled` | Enable Kafka MCP server | `true` |
| `mcpKafka.replicaCount` | Number of replicas | `1` |
| `mcpKafka.image.repository` | Image repository | `agentic-ai/mcp-kafka` |
| `mcpKafka.service.port` | Service port | `8002` |
| `mcpKafka.resources.limits.cpu` | CPU limit | `500m` |
| `mcpKafka.resources.limits.memory` | Memory limit | `512Mi` |

### Consumer Service Configuration

| Parameter | Description | Default |
|-----------|-------------|---------|
| `consumer.enabled` | Enable consumer service | `true` |
| `consumer.replicaCount` | Number of replicas | `2` |
| `consumer.image.repository` | Image repository | `agentic-ai/consumer` |
| `consumer.service.port` | Service port | `8003` |
| `consumer.autoscaling.enabled` | Enable HPA | `true` |
| `consumer.autoscaling.minReplicas` | Minimum replicas | `1` |
| `consumer.autoscaling.maxReplicas` | Maximum replicas | `5` |

### Database Configuration

#### PostgreSQL

| Parameter | Description | Default |
|-----------|-------------|---------|
| `postgresql.enabled` | Enable PostgreSQL | `true` |
| `postgresql.auth.postgresPassword` | Postgres admin password | `change-me` |
| `postgresql.auth.username` | Application username | `agenticai` |
| `postgresql.auth.password` | Application password | `change-me` |
| `postgresql.auth.database` | Database name | `customer_support` |
| `postgresql.primary.persistence.enabled` | Enable persistence | `true` |
| `postgresql.primary.persistence.size` | Storage size | `20Gi` |
| `postgresql.primary.resources.limits.cpu` | CPU limit | `1000m` |
| `postgresql.primary.resources.limits.memory` | Memory limit | `1Gi` |

#### Kafka

| Parameter | Description | Default |
|-----------|-------------|---------|
| `kafka.enabled` | Enable Kafka | `true` |
| `kafka.replicaCount` | Number of Kafka brokers | `3` |
| `kafka.persistence.enabled` | Enable persistence | `true` |
| `kafka.persistence.size` | Storage size | `50Gi` |
| `kafka.resources.limits.cpu` | CPU limit | `1000m` |
| `kafka.resources.limits.memory` | Memory limit | `1Gi` |
| `kafka.zookeeper.replicaCount` | Number of Zookeeper nodes | `3` |
| `kafka.zookeeper.persistence.size` | Zookeeper storage size | `8Gi` |

#### Qdrant Vector Database

| Parameter | Description | Default |
|-----------|-------------|---------|
| `qdrant.enabled` | Enable Qdrant | `true` |
| `qdrant.replicaCount` | Number of replicas | `1` |
| `qdrant.image.repository` | Image repository | `qdrant/qdrant` |
| `qdrant.service.port` | Service port | `6333` |
| `qdrant.persistence.enabled` | Enable persistence | `true` |
| `qdrant.persistence.size` | Storage size | `30Gi` |
| `qdrant.resources.limits.cpu` | CPU limit | `1000m` |
| `qdrant.resources.limits.memory` | Memory limit | `2Gi` |

### Ingress Configuration

| Parameter | Description | Default |
|-----------|-------------|---------|
| `ingress.enabled` | Enable ingress | `true` |
| `ingress.className` | Ingress class | `nginx` |
| `ingress.annotations` | Ingress annotations | See values.yaml |
| `ingress.hosts[0].host` | Hostname | `api.agentic-ai-support.com` |
| `ingress.tls[0].secretName` | TLS secret name | `agentic-ai-tls-secret` |

### Security Configuration

| Parameter | Description | Default |
|-----------|-------------|---------|
| `securityContext.runAsNonRoot` | Run as non-root user | `true` |
| `securityContext.runAsUser` | User ID | `1000` |
| `securityContext.fsGroup` | File system group | `2000` |
| `networkPolicy.enabled` | Enable network policies | `true` |

### High Availability Configuration

| Parameter | Description | Default |
|-----------|-------------|---------|
| `podDisruptionBudget.enabled` | Enable PDB | `true` |
| `podDisruptionBudget.minAvailable` | Minimum available pods | `1` |

### Monitoring Configuration

| Parameter | Description | Default |
|-----------|-------------|---------|
| `monitoring.enabled` | Enable monitoring | `false` |
| `monitoring.serviceMonitor.enabled` | Enable ServiceMonitor | `false` |
| `monitoring.prometheusRule.enabled` | Enable PrometheusRule | `false` |

## Cloud Provider Configurations

### AWS (EKS)

```bash
helm install agentic-ai-support ops/helm/ \
  -f ops/helm/values-aws.yaml \
  --set cloudProvider.aws.enabled=true
```

**AWS-specific features:**
- EBS GP3 storage class
- Network Load Balancer (NLB)
- Application Load Balancer (ALB) ingress
- Multi-AZ pod anti-affinity

### Azure (AKS)

```bash
helm install agentic-ai-support ops/helm/ \
  -f ops/helm/values-azure.yaml \
  --set cloudProvider.azure.enabled=true
```

**Azure-specific features:**
- Premium managed disk storage
- Azure Load Balancer
- Application Gateway ingress
- Azure DNS integration

### Google Cloud (GKE)

```bash
helm install agentic-ai-support ops/helm/ \
  -f ops/helm/values-gcp.yaml \
  --set cloudProvider.gcp.enabled=true
```

**GCP-specific features:**
- SSD persistent disk storage
- External Load Balancer
- GCE ingress controller

## Deployment Scenarios

### Development Environment

```bash
helm install agentic-ai-dev ops/helm/ \
  --set api.replicaCount=1 \
  --set kafka.replicaCount=1 \
  --set postgresql.primary.persistence.size=10Gi \
  --set kafka.persistence.size=20Gi \
  --set monitoring.enabled=false \
  --set ingress.enabled=false
```

### Staging Environment

```bash
helm install agentic-ai-staging ops/helm/ \
  --set api.replicaCount=2 \
  --set kafka.replicaCount=2 \
  --set postgresql.primary.persistence.size=50Gi \
  --set kafka.persistence.size=100Gi \
  --set monitoring.enabled=true
```

### Production Environment

```bash
helm install agentic-ai-prod ops/helm/ \
  -f ops/helm/values-aws.yaml \
  --set api.replicaCount=5 \
  --set api.autoscaling.maxReplicas=20 \
  --set kafka.replicaCount=3 \
  --set postgresql.primary.persistence.size=100Gi \
  --set kafka.persistence.size=200Gi \
  --set monitoring.enabled=true \
  --set networkPolicy.enabled=true
```

## Upgrades

### Upgrade Application

```bash
# Upgrade with new image tags
helm upgrade agentic-ai-support ops/helm/ \
  --set api.image.tag=v1.1.0 \
  --set mcpPostgres.image.tag=v1.1.0 \
  --set mcpKafka.image.tag=v1.1.0 \
  --set consumer.image.tag=v1.1.0
```

### Rollback

```bash
# List revisions
helm history agentic-ai-support

# Rollback to previous version
helm rollback agentic-ai-support 1
```

## Troubleshooting

### Common Issues

#### 1. PostgreSQL Connection Issues

```bash
# Check PostgreSQL pod status
kubectl get pods -l app.kubernetes.io/name=postgresql

# Check PostgreSQL logs
kubectl logs -l app.kubernetes.io/name=postgresql

# Test connection
kubectl run --rm -i --tty postgres-test --image=postgres:13 --restart=Never -- \
  psql -h agentic-ai-support-postgresql -U agenticai -d customer_support
```

#### 2. Kafka Connection Issues

```bash
# Check Kafka pod status
kubectl get pods -l app.kubernetes.io/name=kafka

# Check Kafka logs
kubectl logs -l app.kubernetes.io/name=kafka

# Test Kafka connectivity
kubectl exec -it agentic-ai-support-kafka-0 -- kafka-topics.sh \
  --bootstrap-server localhost:9092 --list
```

#### 3. Ingress Issues

```bash
# Check ingress status
kubectl get ingress

# Check ingress controller logs
kubectl logs -n ingress-nginx -l app.kubernetes.io/name=ingress-nginx

# Verify certificate
kubectl get certificate
kubectl describe certificate agentic-ai-tls-secret
```

### Health Checks

```bash
# Check all pods
kubectl get pods -l app.kubernetes.io/instance=agentic-ai-support

# Check services
kubectl get svc -l app.kubernetes.io/instance=agentic-ai-support

# Check HPA status
kubectl get hpa

# Check PVC status
kubectl get pvc
```

## Customization

### Custom Values File

Create a custom values file for your environment:

```yaml
# custom-values.yaml
api:
  image:
    tag: "v1.2.0"
  resources:
    limits:
      cpu: 2000m
      memory: 2Gi

postgresql:
  auth:
    postgresPassword: "your-secure-password"
    password: "your-app-password"

ingress:
  hosts:
    - host: api.your-domain.com
      paths:
        - path: /
          pathType: Prefix
          service: api
  tls:
    - secretName: your-tls-secret
      hosts:
        - api.your-domain.com
```

Deploy with custom values:

```bash
helm install agentic-ai-support ops/helm/ -f custom-values.yaml
```

### Template Customization

To extend the Helm chart with additional templates:

1. Create template files in `ops/helm/templates/`
2. Use the helper functions from `_helpers.tpl`
3. Follow Kubernetes manifest best practices
4. Test with `helm template` before deployment

## Security Considerations

### Secrets Management

```bash
# Create secrets before deployment
kubectl create secret generic app-secrets \
  --from-literal=database-password=your-secure-password \
  --from-literal=kafka-password=your-kafka-password

# Reference in values
postgresql:
  auth:
    existingSecret: app-secrets
    secretKeys:
      adminPasswordKey: database-password
```

### Network Security

```bash
# Enable network policies
helm upgrade agentic-ai-support ops/helm/ \
  --set networkPolicy.enabled=true
```

### RBAC Configuration

```bash
# Create service account with minimal permissions
apiVersion: v1
kind: ServiceAccount
metadata:
  name: agentic-ai-sa
---
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: agentic-ai-role
rules:
- apiGroups: [""]
  resources: ["configmaps", "secrets"]
  verbs: ["get", "list"]
```

## Performance Tuning

### Resource Optimization

```bash
# Monitor resource usage
kubectl top pods -l app.kubernetes.io/instance=agentic-ai-support

# Adjust resources based on metrics
helm upgrade agentic-ai-support ops/helm/ \
  --set api.resources.requests.cpu=500m \
  --set api.resources.limits.cpu=1500m
```

### Auto-scaling Configuration

```bash
# Configure HPA with custom metrics
helm upgrade agentic-ai-support ops/helm/ \
  --set api.autoscaling.targetCPUUtilizationPercentage=60 \
  --set api.autoscaling.maxReplicas=20
```

## Backup and Disaster Recovery

### Database Backup

```bash
# Create backup job
apiVersion: batch/v1
kind: CronJob
metadata:
  name: postgres-backup
spec:
  schedule: "0 2 * * *"
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: postgres-backup
            image: postgres:13
            command:
            - /bin/bash
            - -c
            - pg_dump -h agentic-ai-support-postgresql -U agenticai customer_support | gzip > /backup/backup-$(date +%Y%m%d).sql.gz
```

### Persistent Volume Snapshots

```bash
# Create volume snapshot
kubectl apply -f - <<EOF
apiVersion: snapshot.storage.k8s.io/v1
kind: VolumeSnapshot
metadata:
  name: postgres-snapshot
spec:
  source:
    persistentVolumeClaimName: data-agentic-ai-support-postgresql-0
EOF
```

## Monitoring and Observability

### Prometheus Integration

```bash
# Enable monitoring
helm upgrade agentic-ai-support ops/helm/ \
  --set monitoring.enabled=true \
  --set monitoring.serviceMonitor.enabled=true
```

### Grafana Dashboards

Import the provided Grafana dashboards for monitoring:
- Application metrics dashboard
- Infrastructure metrics dashboard
- Business metrics dashboard

## Support and Maintenance

### Regular Maintenance Tasks

1. **Weekly**: Review resource utilization and adjust if needed
2. **Monthly**: Update Helm chart dependencies
3. **Quarterly**: Review and update security configurations
4. **Annually**: Review and update disaster recovery procedures

### Getting Help

- Check the troubleshooting section above
- Review Kubernetes events: `kubectl get events`
- Check application logs: `kubectl logs -l app.kubernetes.io/instance=agentic-ai-support`
- Contact support team: team@agentic-ai.com
