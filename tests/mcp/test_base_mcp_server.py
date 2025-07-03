"""
Comprehensive test suite for Base MCP Server.
Tests the abstract base class for MCP servers.
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, Mock, patch
from typing import Dict, Any, List, Optional
from datetime import datetime

from src.mcp.base_mcp_server import BaseMCPServer


class TestBaseMCPServer:
    """Test cases for BaseMCPServer abstract base class."""

    @pytest.fixture
    def concrete_mcp_server(self):
        """Create a concrete implementation of BaseMCPServer for testing."""
        
        class ConcreteMCPServer(BaseMCPServer):
            """Concrete implementation for testing."""
            
            async def start(self):
                self.running = True
                self.logger.info(f"MCP server {self.name} started")
            
            async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
                if tool_name == "test_tool":
                    return {"result": "success", "arguments": arguments}
                elif tool_name == "error_tool":
                    raise Exception("Tool execution failed")
                else:
                    raise ValueError(f"Unknown tool: {tool_name}")
            
            async def get_resource(self, resource_uri: str) -> Dict[str, Any]:
                if resource_uri == "test://resource":
                    return {"uri": resource_uri, "data": "test resource content"}
                elif resource_uri == "test://error":
                    raise Exception("Resource access failed")
                else:
                    raise ValueError(f"Unknown resource: {resource_uri}")
        
        return ConcreteMCPServer(
            server_id="test_server",
            name="TestMCPServer",
            capabilities=["tools", "resources"],
            tools=["test_tool", "error_tool"],
            resources=["test://resource", "test://error"]
        )

    def test_mcp_server_initialization(self, concrete_mcp_server):
        """Test MCP server initialization."""
        assert concrete_mcp_server.server_id == "test_server"
        assert concrete_mcp_server.name == "TestMCPServer"
        assert concrete_mcp_server.capabilities == ["tools", "resources"]
        assert concrete_mcp_server.tools == ["test_tool", "error_tool"]
        assert concrete_mcp_server.resources == ["test://resource", "test://error"]
        assert concrete_mcp_server.running is False
        assert isinstance(concrete_mcp_server.tool_handlers, dict)
        assert isinstance(concrete_mcp_server.resource_handlers, dict)
        assert isinstance(concrete_mcp_server.context, dict)

    def test_default_handlers_registration(self, concrete_mcp_server):
        """Test that default MCP handlers are registered."""
        expected_handlers = [
            'initialize',
            'list_tools',
            'list_resources',
            'call_tool',
            'get_resource'
        ]
        
        for handler in expected_handlers:
            assert handler in concrete_mcp_server.tool_handlers
            assert callable(concrete_mcp_server.tool_handlers[handler])

    @pytest.mark.asyncio
    async def test_start_server(self, concrete_mcp_server):
        """Test starting the MCP server."""
        assert concrete_mcp_server.running is False
        
        await concrete_mcp_server.start()
        
        assert concrete_mcp_server.running is True

    @pytest.mark.asyncio
    async def test_stop_server(self, concrete_mcp_server):
        """Test stopping the MCP server."""
        concrete_mcp_server.running = True
        
        await concrete_mcp_server.stop()
        
        assert concrete_mcp_server.running is False

    @pytest.mark.asyncio
    async def test_set_context(self, concrete_mcp_server):
        """Test setting context for the server."""
        context = {"user_id": "123", "session": "abc"}
        
        await concrete_mcp_server.set_context(context)
        
        assert concrete_mcp_server.context["user_id"] == "123"
        assert concrete_mcp_server.context["session"] == "abc"

    @pytest.mark.asyncio
    async def test_update_context(self, concrete_mcp_server):
        """Test updating existing context."""
        initial_context = {"user_id": "123", "session": "abc"}
        await concrete_mcp_server.set_context(initial_context)
        
        update_context = {"session": "xyz", "role": "admin"}
        await concrete_mcp_server.set_context(update_context)
        
        assert concrete_mcp_server.context["user_id"] == "123"  # Preserved
        assert concrete_mcp_server.context["session"] == "xyz"  # Updated
        assert concrete_mcp_server.context["role"] == "admin"   # Added


class TestMCPServerMessageProcessing:
    """Test message processing functionality in MCP server."""

    @pytest.fixture
    def concrete_mcp_server(self):
        """Create a concrete implementation of BaseMCPServer for testing."""
        
        class ConcreteMCPServer(BaseMCPServer):
            async def start(self):
                self.running = True
            
            async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
                if tool_name == "test_tool":
                    return {"result": "success", "input": arguments}
                raise ValueError(f"Unknown tool: {tool_name}")
            
            async def get_resource(self, resource_uri: str) -> Dict[str, Any]:
                if resource_uri == "test://resource":
                    return {"uri": resource_uri, "content": "test data"}
                raise ValueError(f"Unknown resource: {resource_uri}")
        
        return ConcreteMCPServer("test", "Test", [], ["test_tool"], ["test://resource"])

    @pytest.mark.asyncio
    async def test_process_initialize_message(self, concrete_mcp_server):
        """Test processing initialize message."""
        message = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {}
        }
        
        response = await concrete_mcp_server.process_message(message)
        
        assert response["jsonrpc"] == "2.0"
        assert response["id"] == 1
        assert "result" in response
        assert response["result"]["protocolVersion"] == "1.0"
        assert response["result"]["serverInfo"]["name"] == "Test"

    @pytest.mark.asyncio
    async def test_process_list_tools_message(self, concrete_mcp_server):
        """Test processing list tools message."""
        message = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "list_tools",
            "params": {}
        }
        
        response = await concrete_mcp_server.process_message(message)
        
        assert response["jsonrpc"] == "2.0"
        assert response["id"] == 2
        assert "result" in response
        assert "tools" in response["result"]
        assert len(response["result"]["tools"]) == 1
        assert response["result"]["tools"][0]["name"] == "test_tool"

    @pytest.mark.asyncio
    async def test_process_list_resources_message(self, concrete_mcp_server):
        """Test processing list resources message."""
        message = {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "list_resources",
            "params": {}
        }
        
        response = await concrete_mcp_server.process_message(message)
        
        assert response["jsonrpc"] == "2.0"
        assert response["id"] == 3
        assert "result" in response
        assert "resources" in response["result"]
        assert len(response["result"]["resources"]) == 1
        assert response["result"]["resources"][0]["uri"] == "test://resource"

    @pytest.mark.asyncio
    async def test_process_call_tool_message(self, concrete_mcp_server):
        """Test processing call tool message."""
        message = {
            "jsonrpc": "2.0",
            "id": 4,
            "method": "call_tool",
            "params": {
                "name": "test_tool",
                "arguments": {"param": "value"}
            }
        }
        
        response = await concrete_mcp_server.process_message(message)
        
        assert response["jsonrpc"] == "2.0"
        assert response["id"] == 4
        assert "result" in response
        assert response["result"]["result"] == "success"
        assert response["result"]["input"]["param"] == "value"

    @pytest.mark.asyncio
    async def test_process_get_resource_message(self, concrete_mcp_server):
        """Test processing get resource message."""
        message = {
            "jsonrpc": "2.0",
            "id": 5,
            "method": "get_resource",
            "params": {
                "uri": "test://resource"
            }
        }
        
        response = await concrete_mcp_server.process_message(message)
        
        assert response["jsonrpc"] == "2.0"
        assert response["id"] == 5
        assert "result" in response
        assert response["result"]["uri"] == "test://resource"
        assert response["result"]["content"] == "test data"

    @pytest.mark.asyncio
    async def test_process_unknown_method(self, concrete_mcp_server):
        """Test processing message with unknown method."""
        message = {
            "jsonrpc": "2.0",
            "id": 6,
            "method": "unknown_method",
            "params": {}
        }
        
        response = await concrete_mcp_server.process_message(message)
        
        assert response["jsonrpc"] == "2.0"
        assert response["id"] == 6
        assert "error" in response
        assert response["error"]["code"] == -32601
        assert "Method not found" in response["error"]["message"]

    @pytest.mark.asyncio
    async def test_process_message_with_error(self, concrete_mcp_server):
        """Test processing message that causes an error."""
        message = {
            "jsonrpc": "2.0",
            "id": 7,
            "method": "call_tool",
            "params": {
                "name": "nonexistent_tool",
                "arguments": {}
            }
        }
        
        response = await concrete_mcp_server.process_message(message)
        
        assert response["jsonrpc"] == "2.0"
        assert response["id"] == 7
        assert "error" in response
        assert response["error"]["code"] == -32000
        assert "Unknown tool" in response["error"]["message"]

    @pytest.mark.asyncio
    async def test_process_notification_message(self, concrete_mcp_server):
        """Test processing notification message (no ID)."""
        message = {
            "jsonrpc": "2.0",
            "method": "list_tools",
            "params": {}
        }
        
        response = await concrete_mcp_server.process_message(message)
        
        # Notifications don't return responses
        assert response is None

    @pytest.mark.asyncio
    async def test_last_activity_updated(self, concrete_mcp_server):
        """Test that last activity is updated when processing messages."""
        initial_activity = concrete_mcp_server.last_activity
        
        message = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {}
        }
        
        await concrete_mcp_server.process_message(message)
        
        assert concrete_mcp_server.last_activity != initial_activity
        assert isinstance(concrete_mcp_server.last_activity, datetime)


class TestMCPServerToolHandling:
    """Test tool handling functionality in MCP server."""

    @pytest.fixture
    def concrete_mcp_server(self):
        """Create a concrete implementation with custom tool handling."""
        
        class ConcreteMCPServer(BaseMCPServer):
            async def start(self):
                self.running = True
            
            async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
                if tool_name == "calculator":
                    operation = arguments.get("operation")
                    a = arguments.get("a", 0)
                    b = arguments.get("b", 0)
                    
                    if operation == "add":
                        return {"result": a + b}
                    elif operation == "multiply":
                        return {"result": a * b}
                    else:
                        raise ValueError(f"Unknown operation: {operation}")
                elif tool_name == "echo":
                    return {"echo": arguments.get("message", "")}
                else:
                    raise ValueError(f"Unknown tool: {tool_name}")
            
            async def get_resource(self, resource_uri: str) -> Dict[str, Any]:
                return {"uri": resource_uri, "data": "mock data"}
            
            async def _get_tool_definition(self, tool_name: str) -> Optional[Dict[str, Any]]:
                if tool_name == "calculator":
                    return {
                        "name": "calculator",
                        "description": "Performs basic math operations",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "operation": {"type": "string", "enum": ["add", "multiply"]},
                                "a": {"type": "number"},
                                "b": {"type": "number"}
                            },
                            "required": ["operation", "a", "b"]
                        }
                    }
                elif tool_name == "echo":
                    return {
                        "name": "echo",
                        "description": "Echoes the input message",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "message": {"type": "string"}
                            },
                            "required": ["message"]
                        }
                    }
                return await super()._get_tool_definition(tool_name)
        
        return ConcreteMCPServer("test", "Test", [], ["calculator", "echo"], [])

    @pytest.mark.asyncio
    async def test_tool_execution_success(self, concrete_mcp_server):
        """Test successful tool execution."""
        result = await concrete_mcp_server.call_tool("calculator", {
            "operation": "add",
            "a": 5,
            "b": 3
        })
        
        assert result["result"] == 8

    @pytest.mark.asyncio
    async def test_tool_execution_with_different_params(self, concrete_mcp_server):
        """Test tool execution with different parameters."""
        result = await concrete_mcp_server.call_tool("calculator", {
            "operation": "multiply",
            "a": 4,
            "b": 7
        })
        
        assert result["result"] == 28

    @pytest.mark.asyncio
    async def test_tool_execution_echo(self, concrete_mcp_server):
        """Test echo tool execution."""
        result = await concrete_mcp_server.call_tool("echo", {
            "message": "Hello, MCP!"
        })
        
        assert result["echo"] == "Hello, MCP!"

    @pytest.mark.asyncio
    async def test_tool_execution_invalid_operation(self, concrete_mcp_server):
        """Test tool execution with invalid operation."""
        with pytest.raises(ValueError, match="Unknown operation"):
            await concrete_mcp_server.call_tool("calculator", {
                "operation": "divide",
                "a": 10,
                "b": 2
            })

    @pytest.mark.asyncio
    async def test_tool_execution_unknown_tool(self, concrete_mcp_server):
        """Test execution of unknown tool."""
        with pytest.raises(ValueError, match="Unknown tool"):
            await concrete_mcp_server.call_tool("nonexistent", {})

    @pytest.mark.asyncio
    async def test_get_tool_definitions(self, concrete_mcp_server):
        """Test getting tool definitions."""
        calc_def = await concrete_mcp_server._get_tool_definition("calculator")
        echo_def = await concrete_mcp_server._get_tool_definition("echo")
        
        assert calc_def["name"] == "calculator"
        assert calc_def["description"] == "Performs basic math operations"
        assert "inputSchema" in calc_def
        assert calc_def["inputSchema"]["type"] == "object"
        
        assert echo_def["name"] == "echo"
        assert echo_def["description"] == "Echoes the input message"

    @pytest.mark.asyncio
    async def test_handle_call_tool_with_params(self, concrete_mcp_server):
        """Test _handle_call_tool with parameters."""
        params = {
            "name": "calculator",
            "arguments": {"operation": "add", "a": 10, "b": 15}
        }
        
        result = await concrete_mcp_server._handle_call_tool(params)
        
        assert result["result"] == 25

    @pytest.mark.asyncio
    async def test_handle_call_tool_unknown(self, concrete_mcp_server):
        """Test _handle_call_tool with unknown tool."""
        params = {
            "name": "unknown_tool",
            "arguments": {}
        }
        
        with pytest.raises(ValueError, match="Unknown tool"):
            await concrete_mcp_server._handle_call_tool(params)


class TestMCPServerResourceHandling:
    """Test resource handling functionality in MCP server."""

    @pytest.fixture
    def concrete_mcp_server(self):
        """Create a concrete implementation with custom resource handling."""
        
        class ConcreteMCPServer(BaseMCPServer):
            async def start(self):
                self.running = True
            
            async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
                return {"tool": tool_name, "args": arguments}
            
            async def get_resource(self, resource_uri: str) -> Dict[str, Any]:
                if resource_uri == "config://database":
                    return {
                        "uri": resource_uri,
                        "content": {
                            "host": "localhost",
                            "port": 5432,
                            "database": "testdb"
                        },
                        "mimeType": "application/json"
                    }
                elif resource_uri == "docs://api":
                    return {
                        "uri": resource_uri,
                        "content": "API Documentation Content",
                        "mimeType": "text/plain"
                    }
                else:
                    raise ValueError(f"Unknown resource: {resource_uri}")
            
            async def _get_resource_definition(self, resource_uri: str) -> Optional[Dict[str, Any]]:
                if resource_uri == "config://database":
                    return {
                        "uri": resource_uri,
                        "name": "Database Configuration",
                        "description": "Database connection settings",
                        "mimeType": "application/json"
                    }
                elif resource_uri == "docs://api":
                    return {
                        "uri": resource_uri,
                        "name": "API Documentation",
                        "description": "REST API documentation",
                        "mimeType": "text/plain"
                    }
                return await super()._get_resource_definition(resource_uri)
        
        return ConcreteMCPServer("test", "Test", [], [], ["config://database", "docs://api"])

    @pytest.mark.asyncio
    async def test_resource_access_success(self, concrete_mcp_server):
        """Test successful resource access."""
        result = await concrete_mcp_server.get_resource("config://database")
        
        assert result["uri"] == "config://database"
        assert result["content"]["host"] == "localhost"
        assert result["content"]["port"] == 5432
        assert result["mimeType"] == "application/json"

    @pytest.mark.asyncio
    async def test_resource_access_different_type(self, concrete_mcp_server):
        """Test accessing different type of resource."""
        result = await concrete_mcp_server.get_resource("docs://api")
        
        assert result["uri"] == "docs://api"
        assert result["content"] == "API Documentation Content"
        assert result["mimeType"] == "text/plain"

    @pytest.mark.asyncio
    async def test_resource_access_unknown(self, concrete_mcp_server):
        """Test accessing unknown resource."""
        with pytest.raises(ValueError, match="Unknown resource"):
            await concrete_mcp_server.get_resource("unknown://resource")

    @pytest.mark.asyncio
    async def test_get_resource_definitions(self, concrete_mcp_server):
        """Test getting resource definitions."""
        db_def = await concrete_mcp_server._get_resource_definition("config://database")
        docs_def = await concrete_mcp_server._get_resource_definition("docs://api")
        
        assert db_def["uri"] == "config://database"
        assert db_def["name"] == "Database Configuration"
        assert db_def["mimeType"] == "application/json"
        
        assert docs_def["uri"] == "docs://api"
        assert docs_def["name"] == "API Documentation"
        assert docs_def["mimeType"] == "text/plain"

    @pytest.mark.asyncio
    async def test_handle_get_resource_with_params(self, concrete_mcp_server):
        """Test _handle_get_resource with parameters."""
        params = {"uri": "config://database"}
        
        result = await concrete_mcp_server._handle_get_resource(params)
        
        assert result["uri"] == "config://database"
        assert "content" in result

    @pytest.mark.asyncio
    async def test_handle_get_resource_unknown(self, concrete_mcp_server):
        """Test _handle_get_resource with unknown resource."""
        params = {"uri": "unknown://resource"}
        
        with pytest.raises(ValueError, match="Unknown resource"):
            await concrete_mcp_server._handle_get_resource(params)


class TestMCPServerAbstractMethods:
    """Test abstract methods and inheritance behavior."""

    def test_cannot_instantiate_base_class(self):
        """Test that BaseMCPServer cannot be instantiated directly."""
        with pytest.raises(TypeError):
            BaseMCPServer("test", "Test", [], [], [])

    def test_incomplete_implementation_fails(self):
        """Test that incomplete implementation fails to instantiate."""
        
        with pytest.raises(TypeError):
            class IncompleteMCPServer(BaseMCPServer):
                async def start(self):
                    pass
                # Missing call_tool and get_resource implementations
            
            IncompleteMCPServer("test", "Test", [], [], [])

    def test_abstract_methods_must_be_implemented(self):
        """Test that all abstract methods must be implemented."""
        
        class CompleteMCPServer(BaseMCPServer):
            async def start(self):
                self.running = True
            
            async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
                return {"tool": tool_name}
            
            async def get_resource(self, resource_uri: str) -> Dict[str, Any]:
                return {"uri": resource_uri}
        
        # Should be able to instantiate complete implementation
        server = CompleteMCPServer("test", "Test", [], [], [])
        assert server.name == "Test"

    @pytest.mark.asyncio
    async def test_not_implemented_error_for_base_methods(self):
        """Test that base implementations raise NotImplementedError."""
        
        class PartialMCPServer(BaseMCPServer):
            async def start(self):
                pass
            # Don't implement call_tool and get_resource to test base behavior
        
        # We can't instantiate this due to abstract methods, but we can test the methods directly
        # by temporarily removing the abstractmethod decorators in a mock scenario
        with patch.object(BaseMCPServer, '__abstractmethods__', set()):
            server = BaseMCPServer("test", "Test", [], [], [])
            
            with pytest.raises(NotImplementedError):
                await server.call_tool("test", {})
            
            with pytest.raises(NotImplementedError):
                await server.get_resource("test://resource")


class TestMCPServerLogging:
    """Test logging functionality in MCP server."""

    @pytest.fixture
    def concrete_mcp_server(self):
        """Create a concrete implementation for logging tests."""
        
        class ConcreteMCPServer(BaseMCPServer):
            async def start(self):
                self.running = True
            
            async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
                return {"tool": tool_name}
            
            async def get_resource(self, resource_uri: str) -> Dict[str, Any]:
                return {"uri": resource_uri}
        
        return ConcreteMCPServer("test", "TestServer", [], [], [])

    def test_logger_initialization(self, concrete_mcp_server):
        """Test that logger is properly initialized."""
        assert concrete_mcp_server.logger is not None
        assert concrete_mcp_server.logger.name == "MCP.TestServer"

    @pytest.mark.asyncio
    async def test_error_logging_during_message_processing(self, concrete_mcp_server):
        """Test that errors are logged during message processing."""
        # Mock the tool handler to raise an exception
        concrete_mcp_server.tool_handlers['test_method'] = AsyncMock(side_effect=Exception("Test error"))
        
        message = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "test_method",
            "params": {}
        }
        
        with patch.object(concrete_mcp_server.logger, 'error') as mock_error:
            response = await concrete_mcp_server.process_message(message)
            
            assert "error" in response
            mock_error.assert_called_once()

    @pytest.mark.asyncio
    async def test_info_logging_during_lifecycle(self, concrete_mcp_server):
        """Test info logging during server lifecycle."""
        with patch.object(concrete_mcp_server.logger, 'info') as mock_info:
            await concrete_mcp_server.stop()
            
            mock_info.assert_called_once_with("MCP server TestServer stopped")

    @pytest.mark.asyncio
    async def test_debug_logging_during_context_update(self, concrete_mcp_server):
        """Test debug logging during context updates."""
        with patch.object(concrete_mcp_server.logger, 'debug') as mock_debug:
            await concrete_mcp_server.set_context({"test": "context"})
            
            mock_debug.assert_called_once_with("Context updated for TestServer")
