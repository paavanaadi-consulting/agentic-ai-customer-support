# A2A Protocol Best Practices

## Development Best Practices

### 1. Agent Design Principles

#### Single Responsibility Principle
Each agent should have a clearly defined, single responsibility:

```python
# ✅ Good: Focused responsibility
class SentimentAnalysisAgent(A2AAgent):
    """Analyzes sentiment in customer communications"""
    
    def get_capabilities(self):
        return ['analyze_sentiment', 'detect_emotion', 'assess_satisfaction']

# ❌ Bad: Too many responsibilities
class SuperAgent(A2AAgent):
    """Does everything: sentiment, knowledge, response, analytics"""
    
    def get_capabilities(self):
        return ['analyze_sentiment', 'retrieve_knowledge', 'generate_response', 
                'create_reports', 'manage_users', 'send_emails']
```

#### Clear Message Interfaces
Define clear, well-documented message interfaces:

```python
class CustomerAnalysisAgent(A2AAgent):
    """
    Message Interface:
    
    INPUT: analyze_customer
    - customer_id (str): Unique customer identifier
    - interaction_history (list): Previous interactions
    - context (dict): Additional context data
    
    OUTPUT: customer_analysis
    - profile (dict): Customer profile information
    - preferences (dict): Inferred preferences
    - risk_score (float): Customer risk assessment
    - recommendations (list): Action recommendations
    """
    
    async def _handle_analyze_customer(self, message):
        # Validate input
        required_fields = ['customer_id', 'interaction_history']
        self.validate_message_payload(message, required_fields)
        
        # Process request
        result = await self.analyze_customer(message.payload)
        
        # Send structured response
        await self.send_message(
            receiver_id=message.sender_id,
            message_type="customer_analysis",
            payload=result,
            request_id=message.request_id
        )
```

### 2. Error Handling Best Practices

#### Comprehensive Error Handling
Implement robust error handling with proper classification:

```python
class RobustAgent(A2AAgent):
    """Agent with comprehensive error handling"""
    
    async def _handle_complex_task(self, message):
        try:
            # Validate input
            self.validate_input(message.payload)
            
            # Process task with timeout
            result = await asyncio.wait_for(
                self.process_task(message.payload),
                timeout=self.processing_timeout
            )
            
            # Validate output
            self.validate_output(result)
            
            # Send success response
            await self.send_success_response(message, result)
            
        except ValidationError as e:
            await self.send_error_response(message, f"Invalid input: {e}", "validation_error")
        except TimeoutError:
            await self.send_error_response(message, "Processing timeout", "timeout_error")
        except ResourceError as e:
            await self.send_error_response(message, f"Resource unavailable: {e}", "resource_error")
        except Exception as e:
            self.logger.exception(f"Unexpected error in task processing: {e}")
            await self.send_error_response(message, "Internal processing error", "internal_error")
    
    async def send_error_response(self, original_message, error_message, error_type):
        """Send standardized error response"""
        await self.send_message(
            receiver_id=original_message.sender_id,
            message_type="error",
            payload={
                "error_type": error_type,
                "error_message": error_message,
                "original_message_id": original_message.message_id,
                "agent_id": self.agent_id,
                "timestamp": datetime.now().isoformat(),
                "retry_after": self.get_retry_delay(error_type)
            },
            request_id=original_message.request_id
        )
```

#### Graceful Degradation
Implement fallback mechanisms for critical functionality:

```python
class KnowledgeAgent(A2AAgent):
    """Knowledge agent with fallback mechanisms"""
    
    async def retrieve_knowledge(self, query):
        """Retrieve knowledge with multiple fallback strategies"""
        
        # Primary strategy: Vector database search
        try:
            result = await self.vector_search(query)
            if self.is_result_sufficient(result):
                return result
        except Exception as e:
            self.logger.warning(f"Vector search failed: {e}")
        
        # Fallback 1: Traditional text search
        try:
            result = await self.text_search(query)
            if self.is_result_sufficient(result):
                return result
        except Exception as e:
            self.logger.warning(f"Text search failed: {e}")
        
        # Fallback 2: External API
        try:
            result = await self.external_api_search(query)
            if self.is_result_sufficient(result):
                return result
        except Exception as e:
            self.logger.warning(f"External API search failed: {e}")
        
        # Final fallback: Return cached results or default response
        return self.get_cached_or_default_response(query)
```

### 3. Performance Optimization

#### Message Validation Optimization
Cache validation schemas and use efficient validation:

```python
class OptimizedAgent(A2AAgent):
    """Agent with optimized message validation"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Pre-compile validation schemas
        self.validation_schemas = {
            'analyze_query': {
                'required': ['query', 'customer_id'],
                'optional': ['context', 'priority'],
                'types': {
                    'query': str,
                    'customer_id': (str, int),
                    'priority': str
                }
            }
        }
    
    def validate_message_fast(self, message, message_type):
        """Fast message validation using pre-compiled schemas"""
        schema = self.validation_schemas.get(message_type)
        if not schema:
            return True  # No validation needed
        
        payload = message.payload
        
        # Check required fields
        for field in schema['required']:
            if field not in payload:
                raise ValidationError(f"Missing required field: {field}")
        
        # Check types
        for field, expected_type in schema['types'].items():
            if field in payload and not isinstance(payload[field], expected_type):
                raise ValidationError(f"Invalid type for {field}: expected {expected_type}")
        
        return True
```

#### Connection Management
Implement efficient connection management:

```python
class EfficientAgent(A2AAgent):
    """Agent with efficient connection management"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.connection_pool_size = 20
        self.connection_timeout = 30
        self.keep_alive_interval = 10
        
        # Start connection maintenance task
        asyncio.create_task(self._maintain_connections())
    
    async def _maintain_connections(self):
        """Maintain healthy connections"""
        while self.running:
            try:
                # Clean up stale connections
                stale_connections = []
                for agent_id, connection in self.connections.items():
                    if not connection.open:
                        stale_connections.append(agent_id)
                
                for agent_id in stale_connections:
                    del self.connections[agent_id]
                    self.logger.info(f"Removed stale connection: {agent_id}")
                
                # Send keep-alive to active connections
                for agent_id, connection in self.connections.items():
                    try:
                        await self.send_keep_alive(agent_id)
                    except Exception as e:
                        self.logger.warning(f"Keep-alive failed for {agent_id}: {e}")
                
                await asyncio.sleep(self.keep_alive_interval)
                
            except Exception as e:
                self.logger.error(f"Connection maintenance error: {e}")
                await asyncio.sleep(5)
    
    async def send_keep_alive(self, agent_id):
        """Send keep-alive message"""
        await self.send_message(
            receiver_id=agent_id,
            message_type="keep_alive",
            payload={"timestamp": time.time()}
        )
```

### 4. Testing Best Practices

#### Unit Testing Template
```python
import pytest
import asyncio
from unittest.mock import AsyncMock, patch
from src.a2a_protocol.base_a2a_agent import A2AAgent

class TestAgent(A2AAgent):
    """Test agent for unit testing"""
    
    def __init__(self):
        super().__init__("test_agent", "test", 9999)
        self.message_handlers.update({
            'test_message': self._handle_test_message
        })
        self.test_results = []
    
    async def _handle_test_message(self, message):
        self.test_results.append(message.payload)
        await self.send_message(
            receiver_id=message.sender_id,
            message_type="test_response",
            payload={"received": True},
            request_id=message.request_id
        )

@pytest.fixture
async def test_agent():
    """Fixture for test agent"""
    agent = TestAgent()
    await agent.start()
    yield agent
    await agent.stop()

@pytest.mark.asyncio
async def test_message_handling(test_agent):
    """Test message handling functionality"""
    # Create test message
    from src.a2a_protocol.base_a2a_agent import A2AMessage
    
    message = A2AMessage(
        sender_id="sender",
        receiver_id="test_agent",
        message_type="test_message",
        payload={"data": "test_data"}
    )
    
    # Process message
    await test_agent._process_message(message)
    
    # Verify results
    assert len(test_agent.test_results) == 1
    assert test_agent.test_results[0]["data"] == "test_data"

@pytest.mark.asyncio
async def test_error_handling(test_agent):
    """Test error handling"""
    # Mock a method to raise an exception
    with patch.object(test_agent, '_handle_test_message', side_effect=Exception("Test error")):
        
        message = A2AMessage(
            sender_id="sender",
            receiver_id="test_agent",
            message_type="test_message",
            payload={"data": "test_data"}
        )
        
        # Should not raise exception (error should be handled gracefully)
        await test_agent._process_message(message)
```

#### Integration Testing
```python
@pytest.mark.integration
async def test_multi_agent_workflow():
    """Test complete multi-agent workflow"""
    
    # Setup agents
    coordinator = A2ACoordinator()
    query_agent = A2AQueryAgent(api_key="test_key")
    
    await coordinator.start()
    await query_agent.start()
    
    # Wait for discovery
    await asyncio.sleep(2)
    
    # Test workflow
    result = await coordinator.process_task({
        "task_type": "customer_support_workflow",
        "query_data": {
            "query": "Test query",
            "customer_id": "test_123"
        }
    })
    
    # Verify results
    assert result is not None
    assert result.get("success", False) is True
    
    # Cleanup
    await coordinator.stop()
    await query_agent.stop()
```

### 5. Monitoring and Observability

#### Structured Logging
```python
import structlog

class ObservableAgent(A2AAgent):
    """Agent with comprehensive observability"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Configure structured logging
        self.logger = structlog.get_logger(
            agent_id=self.agent_id,
            agent_type=self.agent_type,
            port=self.port
        )
    
    async def _process_message(self, message):
        """Process message with detailed logging"""
        start_time = time.time()
        
        self.logger.info(
            "message_received",
            message_id=message.message_id,
            sender_id=message.sender_id,
            message_type=message.message_type
        )
        
        try:
            await super()._process_message(message)
            
            processing_time = time.time() - start_time
            self.logger.info(
                "message_processed_successfully",
                message_id=message.message_id,
                processing_time_seconds=processing_time
            )
            
        except Exception as e:
            processing_time = time.time() - start_time
            self.logger.error(
                "message_processing_failed",
                message_id=message.message_id,
                error=str(e),
                error_type=type(e).__name__,
                processing_time_seconds=processing_time
            )
            raise
```

#### Metrics Collection
```python
class MetricsAgent(A2AAgent):
    """Agent with comprehensive metrics collection"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Initialize metrics
        self.detailed_metrics = {
            'message_counts': defaultdict(int),
            'processing_times': defaultdict(list),
            'error_counts': defaultdict(int),
            'throughput': {
                'messages_per_second': 0,
                'last_calculated': time.time()
            }
        }
        
        # Start metrics reporting
        asyncio.create_task(self._report_metrics())
    
    async def _report_metrics(self):
        """Periodically report metrics"""
        while self.running:
            try:
                metrics = self.calculate_current_metrics()
                await self.publish_metrics(metrics)
                await asyncio.sleep(60)  # Report every minute
            except Exception as e:
                self.logger.error(f"Metrics reporting failed: {e}")
                await asyncio.sleep(10)
    
    def calculate_current_metrics(self):
        """Calculate current performance metrics"""
        now = time.time()
        
        # Calculate throughput
        total_messages = sum(self.detailed_metrics['message_counts'].values())
        time_diff = now - self.detailed_metrics['throughput']['last_calculated']
        if time_diff > 0:
            self.detailed_metrics['throughput']['messages_per_second'] = total_messages / time_diff
        
        # Calculate average processing times
        avg_times = {}
        for msg_type, times in self.detailed_metrics['processing_times'].items():
            if times:
                avg_times[msg_type] = sum(times) / len(times)
        
        return {
            'agent_id': self.agent_id,
            'timestamp': now,
            'message_counts': dict(self.detailed_metrics['message_counts']),
            'average_processing_times': avg_times,
            'error_counts': dict(self.detailed_metrics['error_counts']),
            'throughput': self.detailed_metrics['throughput']['messages_per_second'],
            'active_connections': len(self.connections)
        }
```

### 6. Security Best Practices

#### Input Validation and Sanitization
```python
class SecureAgent(A2AAgent):
    """Agent with security best practices"""
    
    def validate_and_sanitize_input(self, payload):
        """Comprehensive input validation and sanitization"""
        
        # Size limits
        if len(str(payload)) > 1_000_000:  # 1MB limit
            raise ValidationError("Payload too large")
        
        # Type validation
        if not isinstance(payload, dict):
            raise ValidationError("Payload must be a dictionary")
        
        # Sanitize string inputs
        sanitized = {}
        for key, value in payload.items():
            if isinstance(value, str):
                # Remove potential script injections
                sanitized[key] = self.sanitize_string(value)
            else:
                sanitized[key] = value
        
        return sanitized
    
    def sanitize_string(self, input_string):
        """Sanitize string input"""
        # Remove HTML tags
        import re
        sanitized = re.sub(r'<[^>]+>', '', input_string)
        
        # Remove potential script content
        sanitized = re.sub(r'javascript:', '', sanitized, flags=re.IGNORECASE)
        
        # Limit length
        return sanitized[:10000]  # 10KB limit
    
    async def _process_message(self, message):
        """Process message with security validation"""
        try:
            # Validate message source
            if not self.is_authorized_sender(message.sender_id):
                raise SecurityError(f"Unauthorized sender: {message.sender_id}")
            
            # Sanitize payload
            message.payload = self.validate_and_sanitize_input(message.payload)
            
            # Rate limiting
            if not self.check_rate_limit(message.sender_id):
                raise RateLimitError(f"Rate limit exceeded for {message.sender_id}")
            
            await super()._process_message(message)
            
        except SecurityError as e:
            self.logger.warning(f"Security violation: {e}")
            await self.send_error_response(message, "Security violation", "security_error")
        except RateLimitError as e:
            self.logger.warning(f"Rate limit exceeded: {e}")
            await self.send_error_response(message, "Rate limit exceeded", "rate_limit_error")
```

### 7. Configuration Management

#### Environment-Based Configuration
```python
class ConfigurableAgent(A2AAgent):
    """Agent with flexible configuration management"""
    
    def __init__(self, *args, **kwargs):
        # Load configuration from environment
        self.config = self.load_configuration()
        
        # Override defaults with config
        port = self.config.get('port', kwargs.get('port', 8000))
        super().__init__(*args, port=port, **kwargs)
        
        # Apply configuration
        self.apply_configuration()
    
    def load_configuration(self):
        """Load configuration from multiple sources"""
        import os
        
        config = {
            # Default values
            'port': 8000,
            'max_connections': 100,
            'message_timeout': 30,
            'log_level': 'INFO',
            'enable_metrics': True
        }
        
        # Override with environment variables
        config.update({
            'port': int(os.getenv('AGENT_PORT', config['port'])),
            'max_connections': int(os.getenv('AGENT_MAX_CONNECTIONS', config['max_connections'])),
            'message_timeout': float(os.getenv('AGENT_MESSAGE_TIMEOUT', config['message_timeout'])),
            'log_level': os.getenv('AGENT_LOG_LEVEL', config['log_level']),
            'enable_metrics': os.getenv('AGENT_ENABLE_METRICS', 'true').lower() == 'true'
        })
        
        # Load from config file if available
        config_file = os.getenv('AGENT_CONFIG_FILE')
        if config_file and os.path.exists(config_file):
            import json
            with open(config_file) as f:
                file_config = json.load(f)
                config.update(file_config)
        
        return config
    
    def apply_configuration(self):
        """Apply configuration to agent"""
        self.max_connections = self.config['max_connections']
        self.message_timeout = self.config['message_timeout']
        
        # Configure logging
        logging.getLogger().setLevel(self.config['log_level'])
        
        # Enable/disable features
        if not self.config['enable_metrics']:
            self.detailed_metrics = None
```

These best practices ensure robust, scalable, and maintainable A2A agent implementations while following industry standards for distributed systems development.
