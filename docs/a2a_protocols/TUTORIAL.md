# A2A Protocol Tutorial

## Tutorial 1: Creating Your First A2A Agent

### Step 1: Basic Agent Setup

Let's create a simple calculator agent that can perform mathematical operations:

```python
# calculator_agent.py
import asyncio
from typing import Dict, Any, List
from src.a2a_protocol.base_a2a_agent import A2AAgent

class CalculatorAgent(A2AAgent):
    """Simple calculator agent for A2A demonstration"""
    
    def __init__(self, agent_id: str = "calculator_agent"):
        super().__init__(agent_id, "calculator", 8006)
        
        # Register our custom message handlers
        self.message_handlers.update({
            'calculate': self._handle_calculation,
            'get_operations': self._handle_operations_request
        })
    
    def get_capabilities(self) -> List[str]:
        """Return list of capabilities"""
        return [
            'addition',
            'subtraction', 
            'multiplication',
            'division',
            'power',
            'square_root'
        ]
    
    async def _handle_calculation(self, message):
        """Handle calculation requests"""
        try:
            payload = message.payload
            operation = payload.get('operation')
            numbers = payload.get('numbers', [])
            
            if not operation or not numbers:
                raise ValueError("Missing operation or numbers")
            
            result = self._perform_calculation(operation, numbers)
            
            await self.send_message(
                receiver_id=message.sender_id,
                message_type="calculation_result",
                payload={
                    "result": result,
                    "operation": operation,
                    "numbers": numbers,
                    "status": "success"
                },
                request_id=message.request_id
            )
            
        except Exception as e:
            await self.send_error_response(message, str(e))
    
    async def _handle_operations_request(self, message):
        """Handle requests for available operations"""
        await self.send_message(
            receiver_id=message.sender_id,
            message_type="operations_list",
            payload={
                "operations": self.get_capabilities(),
                "agent_id": self.agent_id
            },
            request_id=message.request_id
        )
    
    def _perform_calculation(self, operation: str, numbers: List[float]) -> float:
        """Perform the actual calculation"""
        if operation == "addition":
            return sum(numbers)
        elif operation == "subtraction":
            return numbers[0] - sum(numbers[1:])
        elif operation == "multiplication":
            result = 1
            for num in numbers:
                result *= num
            return result
        elif operation == "division":
            result = numbers[0]
            for num in numbers[1:]:
                if num == 0:
                    raise ValueError("Division by zero")
                result /= num
            return result
        elif operation == "power":
            if len(numbers) != 2:
                raise ValueError("Power operation requires exactly 2 numbers")
            return numbers[0] ** numbers[1]
        elif operation == "square_root":
            if len(numbers) != 1:
                raise ValueError("Square root operation requires exactly 1 number")
            if numbers[0] < 0:
                raise ValueError("Cannot calculate square root of negative number")
            return numbers[0] ** 0.5
        else:
            raise ValueError(f"Unknown operation: {operation}")

# Usage example
async def main():
    calc_agent = CalculatorAgent()
    await calc_agent.start()
    
    print(f"Calculator agent started on port {calc_agent.port}")
    print("Agent capabilities:", calc_agent.get_capabilities())
    
    # Keep running
    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        print("Shutting down...")
        await calc_agent.stop()

if __name__ == "__main__":
    asyncio.run(main())
```

### Step 2: Testing the Calculator Agent

Create a test client to interact with your calculator agent:

```python
# test_calculator.py
import asyncio
from src.a2a_protocol.base_a2a_agent import A2AAgent

class TestClient(A2AAgent):
    """Test client for calculator agent"""
    
    def __init__(self):
        super().__init__("test_client", "client", 8007)
        self.message_handlers.update({
            'calculation_result': self._handle_calculation_result,
            'operations_list': self._handle_operations_list
        })
        self.results = {}
    
    async def _handle_calculation_result(self, message):
        """Handle calculation results"""
        payload = message.payload
        print(f"Calculation result: {payload['result']}")
        print(f"Operation: {payload['operation']} on {payload['numbers']}")
        self.results[message.request_id] = payload
    
    async def _handle_operations_list(self, message):
        """Handle operations list"""
        operations = message.payload['operations']
        print(f"Available operations: {operations}")
    
    async def request_calculation(self, operation: str, numbers: List[float]):
        """Request a calculation from calculator agent"""
        await self.send_message(
            receiver_id="calculator_agent",
            message_type="calculate",
            payload={
                "operation": operation,
                "numbers": numbers
            }
        )
    
    async def request_operations(self):
        """Request list of available operations"""
        await self.send_message(
            receiver_id="calculator_agent",
            message_type="get_operations",
            payload={}
        )

async def test_calculator():
    # Start test client
    client = TestClient()
    await client.start()
    
    # Wait for agent discovery
    await asyncio.sleep(2)
    
    # Test various operations
    print("Testing calculator agent...")
    
    # Test addition
    await client.request_calculation("addition", [10, 5, 3])
    await asyncio.sleep(0.5)
    
    # Test multiplication
    await client.request_calculation("multiplication", [4, 3, 2])
    await asyncio.sleep(0.5)
    
    # Test division
    await client.request_calculation("division", [100, 5, 2])
    await asyncio.sleep(0.5)
    
    # Test power
    await client.request_calculation("power", [2, 8])
    await asyncio.sleep(0.5)
    
    # Request operations list
    await client.request_operations()
    await asyncio.sleep(0.5)
    
    # Cleanup
    await client.stop()

if __name__ == "__main__":
    asyncio.run(test_calculator())
```

## Tutorial 2: Multi-Agent Workflow

### Step 1: Create a Data Processing Pipeline

Let's create a workflow with three agents: DataValidator, DataProcessor, and ResultFormatter.

```python
# data_pipeline.py
import asyncio
import json
from typing import Dict, Any, List
from src.a2a_protocol.base_a2a_agent import A2AAgent

class DataValidatorAgent(A2AAgent):
    """Validates incoming data"""
    
    def __init__(self):
        super().__init__("data_validator", "validator", 8008)
        self.message_handlers.update({
            'validate_data': self._handle_validation
        })
    
    async def _handle_validation(self, message):
        """Validate data structure and content"""
        try:
            data = message.payload.get('data')
            validation_result = self._validate_data(data)
            
            await self.send_message(
                receiver_id=message.sender_id,
                message_type="validation_result",
                payload=validation_result,
                request_id=message.request_id
            )
            
        except Exception as e:
            await self.send_error_response(message, str(e))
    
    def _validate_data(self, data) -> Dict[str, Any]:
        """Perform data validation"""
        errors = []
        warnings = []
        
        if not isinstance(data, dict):
            errors.append("Data must be a dictionary")
            return {"valid": False, "errors": errors, "warnings": warnings}
        
        # Check required fields
        required_fields = ['id', 'name', 'value']
        for field in required_fields:
            if field not in data:
                errors.append(f"Missing required field: {field}")
        
        # Validate data types
        if 'id' in data and not isinstance(data['id'], (int, str)):
            errors.append("ID must be a string or integer")
        
        if 'value' in data and not isinstance(data['value'], (int, float)):
            warnings.append("Value should be numeric")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "processed_data": data
        }

class DataProcessorAgent(A2AAgent):
    """Processes validated data"""
    
    def __init__(self):
        super().__init__("data_processor", "processor", 8009)
        self.message_handlers.update({
            'process_data': self._handle_processing
        })
    
    async def _handle_processing(self, message):
        """Process validated data"""
        try:
            data = message.payload.get('data')
            processing_result = self._process_data(data)
            
            await self.send_message(
                receiver_id=message.sender_id,
                message_type="processing_result",
                payload=processing_result,
                request_id=message.request_id
            )
            
        except Exception as e:
            await self.send_error_response(message, str(e))
    
    def _process_data(self, data) -> Dict[str, Any]:
        """Process the data"""
        if not data:
            return {"processed": False, "error": "No data to process"}
        
        # Example processing: normalize and enrich data
        processed = {
            "id": str(data.get('id', 'unknown')),
            "name": data.get('name', '').strip().title(),
            "value": float(data.get('value', 0)),
            "processed_at": asyncio.get_event_loop().time(),
            "metadata": {
                "processing_version": "1.0",
                "original_keys": list(data.keys())
            }
        }
        
        # Add calculated fields
        processed["value_squared"] = processed["value"] ** 2
        processed["name_length"] = len(processed["name"])
        
        return {
            "processed": True,
            "original_data": data,
            "processed_data": processed
        }

class ResultFormatterAgent(A2AAgent):
    """Formats processing results"""
    
    def __init__(self):
        super().__init__("result_formatter", "formatter", 8010)
        self.message_handlers.update({
            'format_result': self._handle_formatting
        })
    
    async def _handle_formatting(self, message):
        """Format processing results"""
        try:
            data = message.payload.get('data')
            format_type = message.payload.get('format', 'json')
            
            formatting_result = self._format_result(data, format_type)
            
            await self.send_message(
                receiver_id=message.sender_id,
                message_type="formatting_result",
                payload=formatting_result,
                request_id=message.request_id
            )
            
        except Exception as e:
            await self.send_error_response(message, str(e))
    
    def _format_result(self, data, format_type: str) -> Dict[str, Any]:
        """Format the result in specified format"""
        if format_type == "json":
            return {
                "format": "json",
                "result": json.dumps(data, indent=2)
            }
        elif format_type == "summary":
            if isinstance(data, dict) and "processed_data" in data:
                processed = data["processed_data"]
                return {
                    "format": "summary",
                    "result": f"ID: {processed.get('id')}, Name: {processed.get('name')}, Value: {processed.get('value')}"
                }
        elif format_type == "table":
            # Simple table format
            if isinstance(data, dict) and "processed_data" in data:
                processed = data["processed_data"]
                table = "| Field | Value |\n|-------|-------|\n"
                for key, value in processed.items():
                    if not isinstance(value, dict):
                        table += f"| {key} | {value} |\n"
                return {
                    "format": "table",
                    "result": table
                }
        
        return {
            "format": format_type,
            "result": str(data)
        }
```

### Step 2: Workflow Orchestrator

```python
# workflow_orchestrator.py
import asyncio
from typing import Dict, Any
from src.a2a_protocol.base_a2a_agent import A2AAgent

class WorkflowOrchestrator(A2AAgent):
    """Orchestrates the data processing workflow"""
    
    def __init__(self):
        super().__init__("workflow_orchestrator", "orchestrator", 8011)
        self.message_handlers.update({
            'process_workflow': self._handle_workflow,
            'validation_result': self._handle_validation_result,
            'processing_result': self._handle_processing_result,
            'formatting_result': self._handle_formatting_result
        })
        self.active_workflows = {}
    
    async def _handle_workflow(self, message):
        """Start a new workflow"""
        workflow_id = message.request_id
        data = message.payload.get('data')
        format_type = message.payload.get('format', 'json')
        
        # Store workflow state
        self.active_workflows[workflow_id] = {
            "requester": message.sender_id,
            "data": data,
            "format": format_type,
            "step": "validation",
            "results": {}
        }
        
        # Step 1: Validate data
        await self.send_message(
            receiver_id="data_validator",
            message_type="validate_data",
            payload={"data": data},
            request_id=workflow_id
        )
    
    async def _handle_validation_result(self, message):
        """Handle validation results and proceed to processing"""
        workflow_id = message.request_id
        workflow = self.active_workflows.get(workflow_id)
        
        if not workflow:
            return
        
        validation_result = message.payload
        workflow["results"]["validation"] = validation_result
        
        if validation_result.get("valid"):
            # Step 2: Process data
            workflow["step"] = "processing"
            await self.send_message(
                receiver_id="data_processor",
                message_type="process_data",
                payload={"data": validation_result["processed_data"]},
                request_id=workflow_id
            )
        else:
            # Validation failed, send error result
            await self._complete_workflow(workflow_id, {
                "success": False,
                "error": "Validation failed",
                "validation_errors": validation_result.get("errors", [])
            })
    
    async def _handle_processing_result(self, message):
        """Handle processing results and proceed to formatting"""
        workflow_id = message.request_id
        workflow = self.active_workflows.get(workflow_id)
        
        if not workflow:
            return
        
        processing_result = message.payload
        workflow["results"]["processing"] = processing_result
        
        if processing_result.get("processed"):
            # Step 3: Format result
            workflow["step"] = "formatting"
            await self.send_message(
                receiver_id="result_formatter",
                message_type="format_result",
                payload={
                    "data": processing_result["processed_data"],
                    "format": workflow["format"]
                },
                request_id=workflow_id
            )
        else:
            # Processing failed
            await self._complete_workflow(workflow_id, {
                "success": False,
                "error": "Processing failed",
                "processing_error": processing_result.get("error")
            })
    
    async def _handle_formatting_result(self, message):
        """Handle formatting results and complete workflow"""
        workflow_id = message.request_id
        workflow = self.active_workflows.get(workflow_id)
        
        if not workflow:
            return
        
        formatting_result = message.payload
        workflow["results"]["formatting"] = formatting_result
        
        # Complete workflow
        await self._complete_workflow(workflow_id, {
            "success": True,
            "result": formatting_result["result"],
            "format": formatting_result["format"],
            "workflow_results": workflow["results"]
        })
    
    async def _complete_workflow(self, workflow_id: str, result: Dict[str, Any]):
        """Complete workflow and send result to requester"""
        workflow = self.active_workflows.get(workflow_id)
        if not workflow:
            return
        
        await self.send_message(
            receiver_id=workflow["requester"],
            message_type="workflow_complete",
            payload=result,
            request_id=workflow_id
        )
        
        # Cleanup
        del self.active_workflows[workflow_id]

# Test the complete workflow
async def test_data_pipeline():
    """Test the complete data processing pipeline"""
    
    # Start all agents
    validator = DataValidatorAgent()
    processor = DataProcessorAgent()
    formatter = ResultFormatterAgent()
    orchestrator = WorkflowOrchestrator()
    
    await validator.start()
    await processor.start()
    await formatter.start()
    await orchestrator.start()
    
    # Create test client
    client = TestClient()
    await client.start()
    
    # Wait for discovery
    await asyncio.sleep(2)
    
    print("Testing data processing pipeline...")
    
    # Test data
    test_data = {
        "id": 123,
        "name": "  john doe  ",
        "value": 42.5,
        "extra_field": "will be preserved"
    }
    
    # Request workflow processing
    await client.send_message(
        receiver_id="workflow_orchestrator",
        message_type="process_workflow",
        payload={
            "data": test_data,
            "format": "summary"
        }
    )
    
    # Wait for completion
    await asyncio.sleep(5)
    
    # Cleanup
    await client.stop()
    await validator.stop()
    await processor.stop()
    await formatter.stop()
    await orchestrator.stop()

if __name__ == "__main__":
    asyncio.run(test_data_pipeline())
```

## Tutorial 3: Advanced Features

### Error Recovery and Resilience

```python
class ResilientAgent(A2AAgent):
    """Agent with advanced error recovery"""
    
    def __init__(self, agent_id: str, agent_type: str, port: int):
        super().__init__(agent_id, agent_type, port)
        self.circuit_breaker = {}  # Simple circuit breaker
        self.retry_config = {
            'max_retries': 3,
            'backoff_factor': 2,
            'timeout': 30
        }
    
    async def send_message_with_circuit_breaker(self, receiver_id: str, message_type: str, payload: Dict[str, Any]):
        """Send message with circuit breaker pattern"""
        
        # Check circuit breaker
        if self._is_circuit_open(receiver_id):
            raise Exception(f"Circuit breaker open for {receiver_id}")
        
        try:
            success = await self.send_message(receiver_id, message_type, payload)
            if success:
                self._reset_circuit_breaker(receiver_id)
            return success
            
        except Exception as e:
            self._record_failure(receiver_id)
            raise e
    
    def _is_circuit_open(self, agent_id: str) -> bool:
        """Check if circuit breaker is open"""
        cb = self.circuit_breaker.get(agent_id, {})
        failure_count = cb.get('failures', 0)
        last_failure = cb.get('last_failure', 0)
        
        # Open circuit if too many failures
        if failure_count >= 5:
            # Close circuit after timeout
            if time.time() - last_failure > 60:  # 1 minute timeout
                self._reset_circuit_breaker(agent_id)
                return False
            return True
        return False
    
    def _record_failure(self, agent_id: str):
        """Record failure for circuit breaker"""
        if agent_id not in self.circuit_breaker:
            self.circuit_breaker[agent_id] = {'failures': 0}
        
        self.circuit_breaker[agent_id]['failures'] += 1
        self.circuit_breaker[agent_id]['last_failure'] = time.time()
    
    def _reset_circuit_breaker(self, agent_id: str):
        """Reset circuit breaker"""
        if agent_id in self.circuit_breaker:
            self.circuit_breaker[agent_id] = {'failures': 0}
```

### Monitoring and Metrics

```python
class MonitoredAgent(A2AAgent):
    """Agent with comprehensive monitoring"""
    
    def __init__(self, agent_id: str, agent_type: str, port: int):
        super().__init__(agent_id, agent_type, port)
        self.detailed_metrics = {
            'message_types': {},
            'response_times': [],
            'error_counts': {},
            'connection_stats': {},
            'resource_usage': {}
        }
        
        # Start monitoring task
        asyncio.create_task(self._monitoring_loop())
    
    async def _monitoring_loop(self):
        """Continuous monitoring loop"""
        while self.running:
            await self._collect_metrics()
            await asyncio.sleep(30)  # Collect metrics every 30 seconds
    
    async def _collect_metrics(self):
        """Collect current metrics"""
        import psutil
        
        # Resource usage
        process = psutil.Process()
        self.detailed_metrics['resource_usage'] = {
            'cpu_percent': process.cpu_percent(),
            'memory_mb': process.memory_info().rss / 1024 / 1024,
            'connections': len(self.connections),
            'timestamp': time.time()
        }
        
        # Log metrics
        self.logger.info(f"Metrics: {self.detailed_metrics['resource_usage']}")
    
    async def _process_message(self, message):
        """Override to add timing and tracking"""
        start_time = time.time()
        
        try:
            await super()._process_message(message)
            
            # Record success metrics
            processing_time = time.time() - start_time
            self.detailed_metrics['response_times'].append(processing_time)
            
            # Track message types
            msg_type = message.message_type
            if msg_type not in self.detailed_metrics['message_types']:
                self.detailed_metrics['message_types'][msg_type] = 0
            self.detailed_metrics['message_types'][msg_type] += 1
            
        except Exception as e:
            # Record error metrics
            error_type = type(e).__name__
            if error_type not in self.detailed_metrics['error_counts']:
                self.detailed_metrics['error_counts'][error_type] = 0
            self.detailed_metrics['error_counts'][error_type] += 1
            raise e
```

This tutorial covers the fundamentals of creating and working with A2A agents. You can extend these examples to build more complex multi-agent systems for your specific use cases.
