# API/Service Integration with PostgreSQL MCP Server

This document explains how the FastAPI service layer is integrated with the PostgreSQL MCP (Model Context Protocol) server for a complete customer support system.

## Overview

The integration provides:
- **MCP Client**: Clean interface for communicating with the PostgreSQL MCP server
- **Service Layer**: Business logic services that use MCP client for data operations
- **Service Factory**: Dependency injection container supporting MCP and in-memory fallbacks
- **API Layer**: FastAPI endpoints that use the service layer
- **Graceful Fallbacks**: System works with in-memory storage if MCP server is unavailable

## Architecture

```
API Routes → Service Factory → Services → MCP Client → MCP Server → PostgreSQL
    ↓              ↓             ↓           ↓
Dependencies  DI Container  Business    Protocol   Database
              ↓             Logic       Layer      Operations
          Fallbacks     MCP/Memory
```

## Components

### 1. MCP Client (`src/data_sources/mcp_client.py`)

The `PostgreSQLMCPClient` class provides:
- **Connection Management**: Async HTTP client for MCP server communication
- **Tool Operations**: Methods for calling MCP tools (create_customer, get_tickets, etc.)
- **Resource Operations**: Methods for reading MCP resources (analytics, summaries)
- **Error Handling**: Custom `MCPClientError` exception handling
- **Singleton Pattern**: Global `get_mcp_client()` function

Key methods:
```python
# Customer operations
await mcp_client.create_customer(customer_data)
await mcp_client.get_customers(limit=100)
await mcp_client.get_customer_by_id(customer_id)
await mcp_client.update_customer(customer_id, updates)

# Ticket operations  
await mcp_client.create_ticket(ticket_data)
await mcp_client.get_tickets(limit=100, status="open")
await mcp_client.get_ticket_by_id(ticket_id)
await mcp_client.update_ticket(ticket_id, updates)

# Analytics and search
await mcp_client.get_analytics(days=30)
await mcp_client.search_knowledge_base(search_term, limit=10)
```

### 2. Service Factory (`src/services/service_factory.py`)

The `ServiceFactory` class manages service instances with:
- **MCP Priority**: Uses MCP client if available
- **Memory Fallback**: Uses in-memory storage as fallback
- **Singleton Services**: Caches service instances
- **Easy Initialization**: Helper functions for different setups

Key functions:
```python
# Initialize with MCP (preferred)
service_factory = await initialize_service_factory_with_mcp()

# Initialize with specific clients
service_factory = initialize_service_factory(mcp_client=mcp_client)

# Get services
customer_service = service_factory.customer_service
ticket_service = service_factory.ticket_service
analytics_service = service_factory.analytics_service
```

### 3. Service Classes

All service classes support the same pattern:
1. **MCP First**: Try MCP client operations
2. **Memory Fallback**: Use in-memory storage
3. **Field Mapping**: Convert between database and API schemas
4. **Error Handling**: Graceful degradation on failures

#### CustomerService (`src/services/customer_service.py`)
- `create_customer()`: Creates new customer records
- `get_customer_by_id()`: Retrieves customer by ID
- `list_customers()`: Lists customers with pagination
- `update_last_interaction()`: Updates interaction timestamps
- `increment_ticket_count()`: Tracks customer activity

#### TicketService (`src/services/ticket_service.py`)
- `create_ticket()`: Creates new support tickets
- `get_ticket_by_id()`: Retrieves ticket details
- `list_tickets()`: Lists tickets with filtering
- `update_ticket_status()`: Updates ticket status and workflow

#### AnalyticsService (`src/services/analytics_service.py`)
- `get_system_analytics()`: Comprehensive system metrics
- Uses MCP analytics tool for database-driven metrics
- Falls back to service aggregation for complex calculations

### 4. API Layer (`src/api/`)

The FastAPI application integrates with services through:
- **Dependency Injection**: Uses service factory for service instances
- **Health Checks**: Monitors MCP server connectivity
- **Error Handling**: Graceful degradation and error responses
- **Startup/Shutdown**: Proper MCP client lifecycle management

Key files:
- `api_main.py`: Application setup with MCP initialization
- `dependencies.py`: Dependency injection for services
- `routes.py`: API endpoints using service layer

## MCP Server Tools

The PostgreSQL MCP server provides these tools:

### Customer Tools
- `create_customer`: Creates new customer records
- `get_customers`: Lists customers with pagination
- `update_customer`: Updates customer information

### Ticket Tools  
- `create_ticket`: Creates new support tickets
- `get_tickets`: Lists tickets with filtering
- `get_ticket_details`: Gets detailed ticket information
- `update_ticket`: Updates ticket information

### Analytics Tools
- `get_analytics`: Provides system analytics and metrics
- `search_knowledge_base`: Searches knowledge articles

### Utility Tools
- `query_database`: Executes custom SQL queries

## Setup and Usage

### 1. Start PostgreSQL MCP Server

```bash
# Start MCP server on port 8001
cd ops/mcp-postgres
python mcp_postgres_main.py
```

### 2. Start Integrated API

```bash
# Option 1: Use startup script (recommended)
python scripts/start_integrated_api.py

# Option 2: Direct API start
python -m src.api.api_main
```

### 3. Test Integration

```bash
# Test MCP server connection
python scripts/test_mcp_postgres.py

# Test full API integration
python scripts/test_api_integration.py
```

## Configuration

### Environment Variables

The system uses these environment variables:

```bash
# MCP Server Configuration
MCP_SERVER_URL=http://localhost:8001

# Database Configuration (for MCP server)
DB_HOST=localhost
DB_PORT=5432
DB_NAME=customer_support
DB_USER=admin
DB_PASSWORD=password

# API Configuration
API_PORT=8000
LOG_LEVEL=INFO
```

### Fallback Behavior

1. **MCP Available**: All operations use MCP server → PostgreSQL
2. **MCP Unavailable**: In-memory operations (development only)

## Error Handling

The system handles errors gracefully:

```python
# Service-level error handling
try:
    customer = await mcp_client.create_customer(data)
except MCPClientError as e:
    # Log error and fall back to in-memory
    logger.warning(f"MCP error: {e}")
    # Use memory fallback
```

## Field Mapping

The system maps between database schema and API schema:

### Customer Mapping
```python
# Database → API
{
    "customer_id": customer["customer_id"],
    "name": f"{customer['first_name']} {customer['last_name']}",
    "email": customer["email"],
    "tier": customer["tier"],
    # ... additional mapping
}
```

### Ticket Mapping
```python
# Database → API  
{
    "ticket_id": ticket["ticket_id"],
    "title": ticket["subject"],  # subject → title
    "priority": Priority(ticket["priority"].upper()),
    "status": TicketStatus(ticket["status"].upper()),
    # ... additional mapping
}
```

## Monitoring and Health Checks

### API Health Check
```bash
curl http://localhost:8000/health
```

Returns:
```json
{
    "status": "healthy",
    "services": {
        "mcp_client": "healthy",
        "service_factory": "initialized"
    }
}
```

### MCP Server Health Check  
```bash
curl http://localhost:8001/health
```

## Development Workflow

1. **Start Dependencies**: PostgreSQL database
2. **Start MCP Server**: `python ops/mcp-postgres/mcp_postgres_main.py`
3. **Test MCP**: `python scripts/test_mcp_postgres.py`
4. **Start API**: `python scripts/start_integrated_api.py`
5. **Test Integration**: `python scripts/test_api_integration.py`

## Production Deployment

For production deployment:

1. **Docker Compose**: Use provided docker-compose files
2. **Environment Variables**: Configure all required variables
3. **Health Checks**: Monitor both API and MCP server health
4. **Scaling**: MCP server can be scaled independently
5. **Monitoring**: Use structured logging and metrics

## Troubleshooting

### Common Issues

1. **MCP Server Connection Failed**
   - Check MCP server is running on port 8001
   - Verify database connectivity
   - Check firewall/network settings

2. **Database Schema Issues**
   - Run database initialization scripts
   - Check table exists and has correct schema
   - Verify user permissions

3. **Import Errors**
   - Install required dependencies (`asyncpg`, `aiohttp`)
   - Check Python path and virtual environment
   - Verify all modules are properly installed

### Debug Commands

```bash
# Test service imports
python -c "from src.services.service_factory import get_service_factory; print('OK')"

# Test MCP client
python -c "from src.data_sources.mcp_client import get_mcp_client; print('OK')"

# Test API startup
python scripts/start_integrated_api.py
```

This integration provides a robust, scalable foundation for the customer support system with proper separation of concerns and graceful fallback mechanisms.
