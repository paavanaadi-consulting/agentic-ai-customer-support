# Scripts Directory

This directory contains all management scripts for the Agentic AI Customer Support Docker infrastructure.

## 🎯 Main Scripts (Recommended)

### `manage.sh` - Interactive Management
The main entry point with an interactive menu for all operations.
```bash
./manage.sh
```

### `health-check.sh` - System Health
Check the health of all services and endpoints.
```bash
./health-check.sh
```

### `logs.sh` - Log Viewer
View logs for any service or all services.
```bash
./logs.sh [service-name]
```

## 🚀 Service Management

### Core Operations
- `build-all.sh` - Build all Docker images
- `start-all.sh` - Start all services
- `stop-all.sh` - Stop all services
- `cleanup-all.sh` - ⚠️ Remove everything (destructive)

### Development
- `start-infrastructure.sh` - Start only infrastructure (DB, Kafka, etc.)
- `stop-infrastructure.sh` - Stop infrastructure services

## 📁 Legacy Scripts

Maintained for backward compatibility:
- `build.sh`, `start.sh`, `stop.sh` - Original management scripts
- `build-api.sh`, `start-api.sh`, `stop-api.sh` - API-specific operations
- `cleanup.sh`, `cleanup-api.sh` - Service-specific cleanup

## 🔧 Usage Examples

```bash
# Interactive management (recommended)
./manage.sh

# Quick development setup
./start-infrastructure.sh

# Build and start everything
./build-all.sh && ./start-all.sh

# Check if everything is working
./health-check.sh

# View API service logs
./logs.sh api-service

# Stop everything
./stop-all.sh

# Nuclear cleanup (removes all data)
./cleanup-all.sh
```

## 📝 Notes

- All scripts are designed to be run from the `cicd/scripts/` directory
- Scripts automatically navigate to the correct working directory
- Most scripts include colored output and progress indicators
- Health checks verify both service status and endpoint availability
