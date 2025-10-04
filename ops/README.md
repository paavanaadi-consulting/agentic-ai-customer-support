# AI Customer Support - Monitoring & CI/CD Setup

This document describes the complete monitoring and CI/CD infrastructure for the AI Customer Support system.

## Architecture Overview

The system includes the following components:

### Core Services
- **PostgreSQL**: Database for customer support data
- **API Service**: FastAPI-based REST API with MCP integration
- **MCP PostgreSQL Server**: Official PostgreSQL MCP server for database operations

### Monitoring Stack
- **Prometheus**: Metrics collection and alerting
- **Grafana**: Visualization and dashboards
- **AlertManager**: Alert routing and notifications
- **Node Exporter**: System metrics
- **PostgreSQL Exporter**: Database metrics

### CI/CD Stack
- **Jenkins**: Continuous integration and deployment
- **Docker**: Containerization
- **Kubernetes**: Orchestration (production)

## Quick Start

### 1. Start All Services

```bash
cd ops
docker-compose -f docker-compose-full.yml up -d
```

### 2. Access Services

| Service | URL | Credentials |
|---------|-----|-------------|
| API | http://localhost:8000 | N/A |
| Grafana | http://localhost:3000 | admin/admin123 |
| Prometheus | http://localhost:9090 | N/A |
| AlertManager | http://localhost:9093 | N/A |
| Jenkins | http://localhost:8080 | admin/admin123 |

### 3. Verify Health

```bash
# Check API health
curl http://localhost:8000/health

# Check Prometheus targets
curl http://localhost:9090/api/v1/targets

# Check Grafana datasource
curl -u admin:admin123 http://localhost:3000/api/datasources
```

## Monitoring

### Metrics Collection

Prometheus collects metrics from:
- API service endpoints
- PostgreSQL database
- System resources (CPU, memory, disk)
- Docker containers

### Dashboards

Grafana provides pre-configured dashboards for:
- API performance and error rates
- Database connections and query performance
- System resource utilization
- Service availability

### Alerting

Alert rules are configured for:
- High error rates (>10% 5xx errors)
- High response times (>2s 95th percentile)
- High database connections (>80)
- High resource usage (>90% memory, >80% CPU)
- Service downtime

### Alert Channels

Alerts can be sent via:
- Email notifications
- Webhook integrations
- Slack (configure webhook URL)
- PagerDuty (configure integration key)

## CI/CD Pipeline

### Jenkins Pipeline Stages

1. **Checkout**: Clone repository
2. **Code Quality**: Linting, formatting, security scans
3. **Test**: Unit tests with coverage reporting
4. **Build**: Docker image builds for all services
5. **Integration Tests**: End-to-end testing
6. **Deploy to Staging**: Kubernetes deployment
7. **Smoke Tests**: Production readiness verification
8. **Deploy to Production**: Manual approval gate

### Pipeline Configuration

The Jenkins pipeline is defined in `Jenkinsfile` and includes:
- Parallel execution for faster builds
- Security scanning with Bandit and Safety
- Code quality checks with Flake8, Black, and isort
- Test coverage reporting
- Docker image building and pushing
- Kubernetes deployments
- Slack/email notifications

### Environment Variables

Required environment variables for CI/CD:
```bash
DOCKER_REGISTRY=your-registry.com
KUBECONFIG=path/to/kubeconfig
SLACK_WEBHOOK_URL=your-slack-webhook
```

## Configuration Files

### Prometheus Configuration
- `monitoring/prometheus.yml`: Main configuration
- `monitoring/alert_rules.yml`: Alert rule definitions

### Grafana Configuration
- `monitoring/grafana.ini`: Grafana settings
- `monitoring/grafana/provisioning/`: Auto-provisioning configs
- `monitoring/grafana/provisioning/dashboards/`: Dashboard definitions

### Jenkins Configuration
- `jenkins/Dockerfile`: Custom Jenkins image
- `jenkins/jenkins.yaml`: Configuration as Code
- `jenkins/plugins.txt`: Required plugins
- `Jenkinsfile`: Pipeline definition

### AlertManager Configuration
- `monitoring/alertmanager.yml`: Alert routing and receivers

## Maintenance

### Backup Strategy

1. **Database Backups**: Automated PostgreSQL backups
2. **Configuration Backups**: Git-based configuration management
3. **Metrics Data**: Prometheus data retention (200h)
4. **Jenkins Data**: Volume-based persistence

### Log Management

Logs are collected from:
- Application containers (`/app/logs`)
- System services (journald)
- Docker containers (docker logs)

### Security Considerations

1. **Secrets Management**: Use Docker secrets or external secret managers
2. **Network Security**: Services communicate within Docker network
3. **Access Control**: Grafana/Jenkins authentication required
4. **Image Security**: Regular base image updates

## Scaling

### Horizontal Scaling

For production deployments:
- Use Kubernetes for auto-scaling
- Configure multiple API service replicas
- Use PostgreSQL read replicas
- Deploy Prometheus in HA mode

### Resource Requirements

Minimum system requirements:
- 8GB RAM
- 4 CPU cores
- 50GB disk space
- Docker and Docker Compose

## Troubleshooting

### Common Issues

1. **Service Won't Start**
   ```bash
   docker-compose logs [service-name]
   ```

2. **Metrics Not Appearing**
   - Check Prometheus targets: http://localhost:9090/targets
   - Verify service endpoints expose `/metrics`

3. **Alerts Not Firing**
   - Check AlertManager status: http://localhost:9093
   - Verify alert rule syntax in Prometheus

4. **Jenkins Build Failures**
   - Check Jenkins logs
   - Verify Docker socket permissions
   - Ensure required credentials are configured

### Health Checks

```bash
# Check all services
docker-compose -f docker-compose-full.yml ps

# Check service logs
docker-compose -f docker-compose-full.yml logs -f [service]

# Check resource usage
docker stats
```

## Development

### Local Development

For development with minimal overhead:
```bash
# Start only core services
docker-compose -f docker-compose-simple.yml up -d

# Start with monitoring
docker-compose -f docker-compose-full.yml up -d prometheus grafana
```

### Adding New Metrics

1. Add metric endpoints to your service
2. Update `prometheus.yml` with new scrape targets
3. Create/update Grafana dashboards
4. Add relevant alert rules

### Custom Dashboards

1. Create dashboards in Grafana UI
2. Export as JSON
3. Save to `monitoring/grafana/provisioning/dashboards/`
4. Restart Grafana to auto-import

## Production Deployment

For production deployment, see:
- `ops/kubernetes/`: Kubernetes manifests
- `ops/helm/`: Helm charts
- `ops/terraform/`: Infrastructure as Code

## Support

For issues and questions:
- Check logs: `docker-compose logs [service]`
- Review metrics: Grafana dashboards
- Monitor alerts: AlertManager interface
- CI/CD status: Jenkins dashboard
