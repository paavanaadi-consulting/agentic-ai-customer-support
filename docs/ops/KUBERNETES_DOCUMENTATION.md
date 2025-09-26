# Kubernetes Infrastructure Documentation

## Overview

The Agentic AI Customer Support system uses a sophisticated Kubernetes infrastructure with both raw manifests and Kustomize overlays for multi-environment deployment. The architecture follows cloud-native best practices for scalability, security, and observability.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    Ingress Controller                        │
│  (nginx/ALB/Application Gateway) + SSL Termination          │
└─────────────────┬───────────────────────────────────────────┘
                  │
    ┌─────────────┼─────────────┐
    │             │             │
    ▼             ▼             ▼
┌─────────┐  ┌─────────┐  ┌─────────┐
│   API   │  │   MCP   │  │Consumer │
│Service  │  │Services │  │Service  │
│(3 pods) │  │(2 pods) │  │(2 pods) │
└─────────┘  └─────────┘  └─────────┘
    │             │             │
    └─────────────┼─────────────┘
                  │
        ┌─────────┼─────────┐
        │         │         │
        ▼         ▼         ▼
  ┌──────────┐ ┌─────┐ ┌─────────┐
  │PostgreSQL│ │Kafka│ │ Qdrant  │
  │(1 master)│ │(3+3)│ │(1 pod)  │
  └──────────┘ └─────┘ └─────────┘
```

## Directory Structure

```
ops/kubernetes/
├── base/                          # Base Kubernetes manifests
│   ├── api-deployment.yaml        # API service deployment
│   ├── api-service.yaml           # API service
│   ├── configmap.yaml             # Application configuration
│   ├── consumer-deployment.yaml   # Consumer service deployment
│   ├── hpa.yaml                   # Horizontal Pod Autoscaling
│   ├── ingress.yaml               # Ingress configuration
│   ├── kafka.yaml                 # Kafka cluster
│   ├── mcp-*.yaml                 # MCP service manifests
│   ├── namespace.yaml             # Namespace definition
│   ├── network-policy.yaml        # Network security policies
│   ├── pod-disruption-budget.yaml # High availability configuration
│   ├── postgres.yaml              # PostgreSQL database
│   ├── qdrant.yaml                # Vector database
│   ├── secrets.yaml               # Secret definitions
│   └── kustomization.yaml         # Kustomize base configuration
└── overlays/                      # Environment-specific customizations
    ├── development/               # Development environment
    ├── staging/                   # Staging environment
    └── production/                # Production environment
        ├── aws/                   # AWS-specific configurations
        ├── azure/                 # Azure-specific configurations
        └── gcp/                   # GCP-specific configurations
```

## Base Manifests

### Namespace Configuration

```yaml
# namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: agentic-ai-support
  labels:
    app.kubernetes.io/name: agentic-ai-customer-support
    app.kubernetes.io/version: "1.0.0"
```

### API Service Deployment

The API service is the main entry point for the application:

**Key Features:**
- **High Availability**: 3 replicas with pod anti-affinity
- **Auto-scaling**: HPA with CPU-based scaling (70% threshold)
- **Resource Management**: CPU and memory limits/requests
- **Security**: Non-root user, security context
- **Health Checks**: Liveness and readiness probes

```yaml
# api-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: api
  namespace: agentic-ai-support
spec:
  replicas: 3
  selector:
    matchLabels:
      app.kubernetes.io/name: api
  template:
    spec:
      securityContext:
        runAsNonRoot: true
        runAsUser: 1000
        fsGroup: 2000
      containers:
      - name: api
        image: agentic-ai-api:latest
        ports:
        - containerPort: 8000
        resources:
          limits:
            cpu: 1000m
            memory: 1Gi
          requests:
            cpu: 250m
            memory: 256Mi
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
```

### MCP Services

Model Context Protocol servers provide specialized data access:

#### PostgreSQL MCP Server
- **Purpose**: Database operations and queries
- **Port**: 8001
- **Replicas**: 1 (stateless)
- **Resources**: 500m CPU, 512Mi memory

#### Kafka MCP Server
- **Purpose**: Event streaming and message processing
- **Port**: 8002
- **Replicas**: 1 (stateless)
- **Resources**: 500m CPU, 512Mi memory

#### AWS MCP Server
- **Purpose**: AWS service integration
- **Ports**: 8766 (Lambda), 8767 (Messaging), 8768 (MQ)
- **Replicas**: 1 (stateless)
- **Resources**: Configurable based on AWS service usage

### Consumer Service

Event processing and AI agent orchestration:

```yaml
# consumer-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: consumer
spec:
  replicas: 2
  template:
    spec:
      containers:
      - name: consumer
        image: agentic-ai-consumer:latest
        ports:
        - containerPort: 8003
        env:
        - name: KAFKA_BOOTSTRAP_SERVERS
          value: "kafka:9092"
        - name: POSTGRES_HOST
          value: "postgres"
        resources:
          limits:
            cpu: 500m
            memory: 512Mi
          requests:
            cpu: 100m
            memory: 256Mi
```

### Database Layer

#### PostgreSQL Primary Database

```yaml
# postgres.yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: postgres
spec:
  serviceName: postgres
  replicas: 1
  template:
    spec:
      containers:
      - name: postgres
        image: postgres:13
        ports:
        - containerPort: 5432
        env:
        - name: POSTGRES_DB
          value: customer_support
        - name: POSTGRES_USER
          valueFrom:
            secretKeyRef:
              name: postgres-secret
              key: username
        - name: POSTGRES_PASSWORD
          valueFrom:
            secretKeyRef:
              name: postgres-secret
              key: password
        volumeMounts:
        - name: postgres-storage
          mountPath: /var/lib/postgresql/data
        resources:
          limits:
            cpu: 1000m
            memory: 1Gi
          requests:
            cpu: 250m
            memory: 256Mi
  volumeClaimTemplates:
  - metadata:
      name: postgres-storage
    spec:
      accessModes: ["ReadWriteOnce"]
      resources:
        requests:
          storage: 20Gi
```

#### Kafka Event Streaming

```yaml
# kafka.yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: kafka
spec:
  serviceName: kafka
  replicas: 3
  template:
    spec:
      containers:
      - name: kafka
        image: bitnami/kafka:latest
        ports:
        - containerPort: 9092
        env:
        - name: KAFKA_CFG_ZOOKEEPER_CONNECT
          value: "zookeeper:2181"
        - name: KAFKA_CFG_ADVERTISED_LISTENERS
          value: "PLAINTEXT://$(POD_NAME).kafka:9092"
        volumeMounts:
        - name: kafka-storage
          mountPath: /bitnami/kafka
        resources:
          limits:
            cpu: 1000m
            memory: 1Gi
          requests:
            cpu: 250m
            memory: 512Mi
  volumeClaimTemplates:
  - metadata:
      name: kafka-storage
    spec:
      accessModes: ["ReadWriteOnce"]
      resources:
        requests:
          storage: 50Gi
```

#### Qdrant Vector Database

```yaml
# qdrant.yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: qdrant
spec:
  serviceName: qdrant
  replicas: 1
  template:
    spec:
      containers:
      - name: qdrant
        image: qdrant/qdrant:latest
        ports:
        - containerPort: 6333
        - containerPort: 6334
        volumeMounts:
        - name: qdrant-storage
          mountPath: /qdrant/storage
        resources:
          limits:
            cpu: 1000m
            memory: 2Gi
          requests:
            cpu: 250m
            memory: 512Mi
  volumeClaimTemplates:
  - metadata:
      name: qdrant-storage
    spec:
      accessModes: ["ReadWriteOnce"]
      resources:
        requests:
          storage: 30Gi
```

### Ingress Configuration

Multi-service ingress with SSL termination:

```yaml
# ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: agentic-ai-ingress
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
    cert-manager.io/cluster-issuer: letsencrypt-prod
spec:
  ingressClassName: nginx
  tls:
  - hosts:
    - api.agentic-ai-support.com
    secretName: agentic-ai-tls-secret
  rules:
  - host: api.agentic-ai-support.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: api
            port:
              number: 8000
      - path: /mcp/postgres
        pathType: Prefix
        backend:
          service:
            name: mcp-postgres
            port:
              number: 8001
      - path: /mcp/kafka
        pathType: Prefix
        backend:
          service:
            name: mcp-kafka
            port:
              number: 8002
```

### Auto-scaling Configuration

```yaml
# hpa.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: api-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: api
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

### High Availability Configuration

```yaml
# pod-disruption-budget.yaml
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: api-pdb
spec:
  minAvailable: 1
  selector:
    matchLabels:
      app.kubernetes.io/name: api
```

### Network Security

```yaml
# network-policy.yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: agentic-ai-network-policy
spec:
  podSelector: {}
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: ingress-nginx
  - from:
    - podSelector: {}
  egress:
  - to: []
    ports:
    - protocol: TCP
      port: 53
    - protocol: UDP
      port: 53
  - to:
    - podSelector: {}
```

## Environment Overlays

### Development Environment

Located in `overlays/development/`:

**Characteristics:**
- Reduced resource requirements
- Single replicas for most services
- Disabled monitoring
- Local storage classes
- HTTP-only ingress (no SSL)

```yaml
# kustomization.yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

resources:
- ../../base

patchesStrategicMerge:
- api-deployment-patch.yaml
- postgres-patch.yaml
- kafka-patch.yaml

patches:
- target:
    kind: Deployment
    name: api
  patch: |-
    - op: replace
      path: /spec/replicas
      value: 1
```

### Staging Environment

Located in `overlays/staging/`:

**Characteristics:**
- Production-like resource allocation
- Full monitoring enabled
- SSL certificates
- Medium-scale storage
- Performance testing configurations

### Production Environment

Located in `overlays/production/` with cloud-specific subdirectories:

#### AWS Production (`production/aws/`)

```yaml
# service-patch.yaml
apiVersion: v1
kind: Service
metadata:
  name: api
  annotations:
    service.beta.kubernetes.io/aws-load-balancer-type: nlb
    service.beta.kubernetes.io/aws-load-balancer-cross-zone-load-balancing-enabled: "true"
spec:
  type: LoadBalancer
```

```yaml
# ingress-patch.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: agentic-ai-ingress
  annotations:
    kubernetes.io/ingress.class: alb
    alb.ingress.kubernetes.io/scheme: internet-facing
    alb.ingress.kubernetes.io/target-type: ip
    alb.ingress.kubernetes.io/listen-ports: '[{"HTTP": 80}, {"HTTPS": 443}]'
```

#### Azure Production (`production/azure/`)

```yaml
# service-patch.yaml
apiVersion: v1
kind: Service
metadata:
  name: api
  annotations:
    service.beta.kubernetes.io/azure-load-balancer-internal: "false"
    service.beta.kubernetes.io/azure-pip-name: "agentic-ai-api-pip"
spec:
  type: LoadBalancer
```

#### GCP Production (`production/gcp/`)

```yaml
# service-patch.yaml
apiVersion: v1
kind: Service
metadata:
  name: api
  annotations:
    cloud.google.com/load-balancer-type: External
spec:
  type: LoadBalancer
```

## Deployment Procedures

### Prerequisites

1. **Kubernetes Cluster**: 1.20+ with sufficient resources
2. **kubectl**: Configured to access your cluster
3. **Kustomize**: For environment-specific deployments
4. **Ingress Controller**: nginx, ALB, or Application Gateway
5. **Cert-manager**: For SSL certificate management

### Base Deployment

```bash
# Deploy base configuration
kubectl apply -k ops/kubernetes/base/

# Verify deployment
kubectl get all -n agentic-ai-support
```

### Environment-Specific Deployment

```bash
# Development
kubectl apply -k ops/kubernetes/overlays/development/

# Staging
kubectl apply -k ops/kubernetes/overlays/staging/

# Production (AWS)
kubectl apply -k ops/kubernetes/overlays/production/aws/
```

### Rolling Updates

```bash
# Update API image
kubectl set image deployment/api api=agentic-ai/api:v1.1.0 -n agentic-ai-support

# Check rollout status
kubectl rollout status deployment/api -n agentic-ai-support

# Rollback if needed
kubectl rollout undo deployment/api -n agentic-ai-support
```

## Configuration Management

### ConfigMaps

```yaml
# configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-config
data:
  API_HOST: "0.0.0.0"
  API_PORT: "8000"
  LOG_LEVEL: "INFO"
  MCP_POSTGRES_URL: "http://mcp-postgres:8001"
  MCP_KAFKA_URL: "http://mcp-kafka:8002"
  KAFKA_BOOTSTRAP_SERVERS: "kafka:9092"
  POSTGRES_HOST: "postgres"
  POSTGRES_PORT: "5432"
  POSTGRES_DB: "customer_support"
  QDRANT_HOST: "qdrant"
  QDRANT_PORT: "6333"
```

### Secrets Management

```yaml
# secrets.yaml
apiVersion: v1
kind: Secret
metadata:
  name: app-secrets
type: Opaque
stringData:
  DATABASE_URL: "postgresql://agenticai:password@postgres:5432/customer_support"
  POSTGRES_PASSWORD: "change-me-in-production"
  KAFKA_PASSWORD: "change-me-in-production"
  API_SECRET_KEY: "change-me-in-production"
```

**Production Secret Management:**

```bash
# Create secrets from files
kubectl create secret generic app-secrets \
  --from-file=database-password=./secrets/db-password.txt \
  --from-file=api-secret-key=./secrets/api-key.txt \
  -n agentic-ai-support

# Or use external secret management
kubectl apply -f external-secrets.yaml
```

## Monitoring and Observability

### Health Checks

```bash
# Check pod health
kubectl get pods -n agentic-ai-support

# Check detailed pod status
kubectl describe pod <pod-name> -n agentic-ai-support

# Check events
kubectl get events -n agentic-ai-support --sort-by=.metadata.creationTimestamp
```

### Logging

```bash
# View application logs
kubectl logs -f deployment/api -n agentic-ai-support

# View logs from all containers in deployment
kubectl logs -f deployment/api -n agentic-ai-support --all-containers=true

# Stream logs from multiple deployments
kubectl logs -f -l app.kubernetes.io/name=agentic-ai-customer-support -n agentic-ai-support
```

### Metrics Collection

```yaml
# ServiceMonitor for Prometheus
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: agentic-ai-metrics
spec:
  selector:
    matchLabels:
      app.kubernetes.io/name: agentic-ai-customer-support
  endpoints:
  - port: metrics
    path: /metrics
    interval: 30s
```

## Performance Optimization

### Resource Tuning

```bash
# Monitor resource usage
kubectl top pods -n agentic-ai-support
kubectl top nodes

# Adjust resources based on usage
kubectl patch deployment api -n agentic-ai-support -p '{"spec":{"template":{"spec":{"containers":[{"name":"api","resources":{"requests":{"cpu":"500m","memory":"512Mi"},"limits":{"cpu":"1500m","memory":"1.5Gi"}}}]}}}}'
```

### Database Optimization

```yaml
# PostgreSQL configuration
apiVersion: v1
kind: ConfigMap
metadata:
  name: postgres-config
data:
  postgresql.conf: |
    shared_preload_libraries = 'pg_stat_statements'
    max_connections = 200
    shared_buffers = 256MB
    effective_cache_size = 1GB
    maintenance_work_mem = 64MB
    checkpoint_completion_target = 0.7
    wal_buffers = 7864kB
    default_statistics_target = 100
    random_page_cost = 1.1
    effective_io_concurrency = 200
```

### Kafka Optimization

```yaml
# Kafka configuration
env:
- name: KAFKA_HEAP_OPTS
  value: "-Xmx512m -Xms512m"
- name: KAFKA_CFG_NUM_NETWORK_THREADS
  value: "8"
- name: KAFKA_CFG_NUM_IO_THREADS
  value: "16"
- name: KAFKA_CFG_SOCKET_SEND_BUFFER_BYTES
  value: "102400"
- name: KAFKA_CFG_SOCKET_RECEIVE_BUFFER_BYTES
  value: "102400"
- name: KAFKA_CFG_SOCKET_REQUEST_MAX_BYTES
  value: "104857600"
```

## Security Best Practices

### Pod Security Standards

```yaml
# Pod Security Context
securityContext:
  runAsNonRoot: true
  runAsUser: 1000
  fsGroup: 2000
  seccompProfile:
    type: RuntimeDefault
  capabilities:
    drop:
    - ALL
  readOnlyRootFilesystem: true
  allowPrivilegeEscalation: false
```

### Network Policies

```yaml
# Strict network policy
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: strict-network-policy
spec:
  podSelector: {}
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          app.kubernetes.io/name: ingress-nginx
    ports:
    - protocol: TCP
      port: 8000
  egress:
  - to:
    - podSelector:
        matchLabels:
          app.kubernetes.io/name: postgres
    ports:
    - protocol: TCP
      port: 5432
```

### RBAC Configuration

```yaml
# Service Account
apiVersion: v1
kind: ServiceAccount
metadata:
  name: agentic-ai-sa

---
# Role
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: agentic-ai-role
rules:
- apiGroups: [""]
  resources: ["configmaps", "secrets"]
  verbs: ["get", "list"]
- apiGroups: [""]
  resources: ["pods"]
  verbs: ["get", "list", "watch"]

---
# RoleBinding
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: agentic-ai-binding
subjects:
- kind: ServiceAccount
  name: agentic-ai-sa
roleRef:
  kind: Role
  name: agentic-ai-role
  apiGroup: rbac.authorization.k8s.io
```

## Backup and Disaster Recovery

### Database Backup

```yaml
# Backup CronJob
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
            - |
              pg_dump -h postgres -U agenticai -d customer_support | \
              gzip > /backup/backup-$(date +%Y%m%d-%H%M%S).sql.gz
            volumeMounts:
            - name: backup-storage
              mountPath: /backup
            env:
            - name: PGPASSWORD
              valueFrom:
                secretKeyRef:
                  name: app-secrets
                  key: postgres-password
          volumes:
          - name: backup-storage
            persistentVolumeClaim:
              claimName: backup-pvc
          restartPolicy: OnFailure
```

### Volume Snapshots

```yaml
# VolumeSnapshot
apiVersion: snapshot.storage.k8s.io/v1
kind: VolumeSnapshot
metadata:
  name: postgres-snapshot
spec:
  source:
    persistentVolumeClaimName: postgres-storage-postgres-0
---
# VolumeSnapshotClass
apiVersion: snapshot.storage.k8s.io/v1
kind: VolumeSnapshotClass
metadata:
  name: csi-snapclass
driver: ebs.csi.aws.com
deletionPolicy: Retain
```

## Troubleshooting Guide

### Common Issues

#### 1. Pod Startup Failures

```bash
# Check pod status
kubectl get pods -n agentic-ai-support

# Describe problematic pod
kubectl describe pod <pod-name> -n agentic-ai-support

# Check logs
kubectl logs <pod-name> -n agentic-ai-support

# Common fixes:
# - Check resource limits
# - Verify image availability
# - Check ConfigMap/Secret references
```

#### 2. Service Connectivity Issues

```bash
# Test service connectivity
kubectl run test-pod --rm -i --tty --image=busybox -- /bin/sh
# Inside pod: wget -qO- http://api:8000/health

# Check service endpoints
kubectl get endpoints -n agentic-ai-support

# Check DNS resolution
kubectl run dns-test --rm -i --tty --image=busybox -- nslookup api.agentic-ai-support.svc.cluster.local
```

#### 3. Database Connection Issues

```bash
# Test database connectivity
kubectl run postgres-test --rm -i --tty --image=postgres:13 -- \
  psql -h postgres -U agenticai -d customer_support

# Check database logs
kubectl logs statefulset/postgres -n agentic-ai-support

# Verify secrets
kubectl get secret app-secrets -n agentic-ai-support -o yaml
```

#### 4. Ingress Issues

```bash
# Check ingress status
kubectl get ingress -n agentic-ai-support

# Describe ingress
kubectl describe ingress agentic-ai-ingress -n agentic-ai-support

# Check ingress controller logs
kubectl logs -n ingress-nginx -l app.kubernetes.io/name=ingress-nginx

# Test SSL certificate
kubectl get certificate -n agentic-ai-support
kubectl describe certificate agentic-ai-tls-secret -n agentic-ai-support
```

### Performance Issues

```bash
# Check resource usage
kubectl top pods -n agentic-ai-support
kubectl top nodes

# Check HPA status
kubectl get hpa -n agentic-ai-support

# Check pod disruption budgets
kubectl get pdb -n agentic-ai-support

# Check node capacity
kubectl describe nodes
```

## Maintenance Procedures

### Regular Maintenance

#### Weekly Tasks
1. Review resource utilization
2. Check log aggregation and rotation
3. Verify backup completion
4. Review security alerts

#### Monthly Tasks
1. Update base images
2. Review and update resource requests/limits
3. Check certificate expiration
4. Review and update network policies

#### Quarterly Tasks
1. Kubernetes cluster updates
2. Security audit
3. Disaster recovery testing
4. Performance benchmarking

### Upgrade Procedures

```bash
# 1. Update images
kubectl set image deployment/api api=agentic-ai/api:v1.2.0 -n agentic-ai-support

# 2. Monitor rollout
kubectl rollout status deployment/api -n agentic-ai-support

# 3. Verify application health
kubectl get pods -n agentic-ai-support
curl -f https://api.agentic-ai-support.com/health

# 4. Rollback if issues
kubectl rollout undo deployment/api -n agentic-ai-support
```

## Advanced Configurations

### Multi-Cluster Deployment

For global availability, deploy across multiple clusters:

```yaml
# cluster-1 (us-east-1)
apiVersion: v1
kind: Service
metadata:
  name: api
  annotations:
    service.beta.kubernetes.io/aws-load-balancer-cross-zone-load-balancing-enabled: "true"

# cluster-2 (eu-west-1)
apiVersion: v1
kind: Service
metadata:
  name: api
  annotations:
    service.beta.kubernetes.io/aws-load-balancer-cross-zone-load-balancing-enabled: "true"
```

### GitOps Integration

```yaml
# ArgoCD Application
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: agentic-ai-support
spec:
  project: default
  source:
    repoURL: https://github.com/agentic-ai/customer-support
    targetRevision: main
    path: ops/kubernetes/overlays/production/aws
  destination:
    server: https://kubernetes.default.svc
    namespace: agentic-ai-support
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
```

This Kubernetes infrastructure provides a robust, scalable, and secure foundation for the Agentic AI Customer Support system across multiple cloud environments.
