# A2A Protocol Quick Reference

## Message Types Quick Reference

### Discovery & Capability Messages
```python
# Discover agents
await agent.send_message("broadcast", "discovery_request", {})

# Query capabilities
await agent.send_message("target_agent", "capability_query", {})

# Response with capabilities
await agent.send_message("requester", "capability_response", {
    "capabilities": ["analyze_query", "extract_entities"]
})
```

### Task Messages
```python
# Request task execution
await agent.send_message("worker_agent", "task_delegation", {
    "task_type": "analyze_query",
    "data": {"query": "user input"},
    "priority": "high"
})

# Return task result
await agent.send_message("requester", "task_result", {
    "result": {"analysis": "..."},
    "status": "success",
    "execution_time": 1.5
})
```

### Collaboration Messages
```python
# Request collaboration
await agent.send_message("partner_agent", "collaboration_request", {
    "workflow_id": "workflow_123",
    "collaboration_type": "sequential",
    "tasks": ["analyze", "synthesize"]
})

# Accept/decline collaboration
await agent.send_message("requester", "collaboration_response", {
    "accepted": True,
    "availability": "immediate",
    "estimated_time": 5.0
})
```

## Agent Ports Reference

| Agent Type | Default Port | Purpose |
|------------|--------------|---------|
| Query Agent | 8001 | Query analysis and preprocessing |
| Knowledge Agent | 8002 | Information retrieval and synthesis |
| Response Agent | 8003 | Response generation and formatting |
| Coordinator | 8004 | Workflow orchestration |
| Custom Agents | 8005+ | User-defined agents |

## Common Message Handlers

### Essential Handlers (Auto-registered)
- `discovery_request` - Handle agent discovery
- `discovery_response` - Process discovery responses
- `capability_query` - Respond to capability queries
- `collaboration_request` - Handle collaboration requests
- `task_delegation` - Process delegated tasks
- `error` - Handle error messages

### Custom Handler Template
```python
async def _handle_custom_message(self, message):
    """Handle custom message type"""
    try:
        # Validate message
        required_fields = ["field1", "field2"]
        self.validate_message_payload(message, required_fields)
        
        # Process message
        result = await self.process_custom_task(message.payload)
        
        # Send response
        await self.send_message(
            receiver_id=message.sender_id,
            message_type="custom_response",
            payload={"result": result},
            request_id=message.request_id
        )
        
    except Exception as e:
        await self.send_error_response(message, str(e))

# Register handler
self.message_handlers["custom_message"] = self._handle_custom_message
```

## Genetic Algorithm Integration

### Gene Template Example
```python
def _get_default_gene_template(self):
    """Define agent's genetic parameters"""
    return {
        'confidence_threshold': 0.7,
        'processing_timeout': 30.0,
        'max_retries': 3,
        'batch_size': 10,
        'optimization_mode': 'balanced'
    }

def _get_gene_ranges(self):
    """Define parameter ranges for evolution"""
    return {
        'confidence_threshold': (0.5, 0.95),
        'processing_timeout': (10.0, 60.0),
        'max_retries': [1, 2, 3, 4, 5],
        'batch_size': [5, 10, 15, 20],
        'optimization_mode': ['speed', 'balanced', 'accuracy']
    }
```

### Applying Chromosome
```python
def set_chromosome(self, chromosome):
    """Apply genetic parameters"""
    self.current_chromosome = chromosome
    
    # Update agent parameters
    if chromosome and chromosome.genes:
        self.confidence_threshold = chromosome.genes.get(
            'confidence_threshold', 
            self.confidence_threshold
        )
        self.processing_timeout = chromosome.genes.get(
            'processing_timeout', 
            self.processing_timeout
        )
```

## Error Handling Patterns

### Standard Error Response
```python
async def send_error_response(self, original_message, error_message):
    """Send standardized error response"""
    await self.send_message(
        receiver_id=original_message.sender_id,
        message_type="error",
        payload={
            "error": error_message,
            "original_message_id": original_message.message_id,
            "agent_id": self.agent_id,
            "timestamp": datetime.now().isoformat()
        },
        request_id=original_message.request_id
    )
```

### Retry Logic
```python
async def send_message_with_retry(self, receiver_id, message_type, payload, max_retries=3):
    """Send message with automatic retry"""
    for attempt in range(max_retries):
        try:
            success = await self.send_message(receiver_id, message_type, payload)
            if success:
                return True
        except Exception as e:
            if attempt == max_retries - 1:
                self.logger.error(f"Failed to send message after {max_retries} attempts: {e}")
                return False
            await asyncio.sleep(2 ** attempt)  # Exponential backoff
    return False
```

## Performance Monitoring

### Metrics Collection
```python
def update_metrics(self, message_type, success=True, processing_time=None):
    """Update agent performance metrics"""
    if message_type == "sent":
        self.metrics['messages_sent'] += 1
    elif message_type == "received":
        self.metrics['messages_received'] += 1
    
    if success:
        self.metrics['successful_operations'] += 1
    else:
        self.metrics['failed_operations'] += 1
    
    if processing_time:
        self.metrics['total_processing_time'] += processing_time
        self.metrics['average_processing_time'] = (
            self.metrics['total_processing_time'] / 
            self.metrics['successful_operations']
        )
```

### Health Check Implementation
```python
async def health_check(self):
    """Return agent health status"""
    return {
        "agent_id": self.agent_id,
        "status": "healthy" if self.running else "stopped",
        "uptime": time.time() - self.start_time,
        "connections": len(self.connections),
        "metrics": self.metrics,
        "memory_usage": self.get_memory_usage(),
        "last_activity": self.last_activity_time
    }
```

## Testing Patterns

### Unit Test Template
```python
import pytest
import asyncio
from src.a2a_protocol.base_a2a_agent import A2AAgent

@pytest.fixture
async def test_agent():
    agent = A2AAgent("test_agent", "test", 8999)
    await agent.start()
    yield agent
    await agent.stop()

@pytest.mark.asyncio
async def test_message_sending(test_agent):
    # Test message sending functionality
    result = await test_agent.send_message(
        "target_agent", 
        "test_message", 
        {"data": "test"}
    )
    assert result is not None

@pytest.mark.asyncio
async def test_message_handling(test_agent):
    # Test message handling
    received_messages = []
    
    async def test_handler(message):
        received_messages.append(message)
    
    test_agent.message_handlers["test_type"] = test_handler
    
    # Simulate message reception
    # ... test implementation
```

## Environment Configuration

### Development Setup
```bash
# Set environment variables
export A2A_LOG_LEVEL=DEBUG
export A2A_DISCOVERY_TIMEOUT=10
export A2A_MESSAGE_RETRY_COUNT=3

# Start agents in development mode
python -m src.a2a_protocol.a2a_coordinator &
python -m src.a2a_protocol.a2a_query_agent &
python -m src.a2a_protocol.a2a_knowledge_agent &
python -m src.a2a_protocol.a2a_response_agent &
```

### Production Configuration
```python
# Production agent configuration
class ProductionAgentConfig:
    LOG_LEVEL = "INFO"
    DISCOVERY_TIMEOUT = 30
    MESSAGE_TIMEOUT = 60
    MAX_CONNECTIONS = 100
    HEALTH_CHECK_INTERVAL = 30
    METRICS_COLLECTION = True
    RETRY_COUNT = 5
    EXPONENTIAL_BACKOFF = True
```
