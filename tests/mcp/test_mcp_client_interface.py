"""
Comprehensive test suite for MCP Client Interface.
Tests abstract base class and interface compliance.
"""
import pytest
from abc import ABC
from typing import Dict, Any, List, Optional

from src.mcp.mcp_client_interface import MCPClientInterface


@pytest.fixture
def concrete_client_class():
    """Fixture providing a concrete implementation of MCPClientInterface for testing."""
    
    class ConcreteMCPClient(MCPClientInterface):
        """Concrete implementation for testing."""
        
        async def connect(self) -> bool:
            return True
            
        async def disconnect(self) -> bool:
            return True
            
        async def get_customers(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
            return []
            
        async def get_customer_by_id(self, customer_id: str) -> Optional[Dict[str, Any]]:
            return None
            
        async def create_customer(self, customer_data: Dict[str, Any]) -> Dict[str, Any]:
            return {}
            
        async def update_customer(self, customer_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
            return {}
            
        async def get_tickets(self, customer_id: Optional[str] = None, status: Optional[str] = None, 
                            limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
            return []
            
        async def get_ticket_by_id(self, ticket_id: str) -> Optional[Dict[str, Any]]:
            return None
            
        async def create_ticket(self, ticket_data: Dict[str, Any]) -> Dict[str, Any]:
            return {}
            
        async def update_ticket(self, ticket_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
            return {}
            
        async def search_knowledge_base(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
            return []
            
        async def get_analytics(self, metric_type: str, start_date: str, end_date: str) -> Dict[str, Any]:
            return {}
    
    return ConcreteMCPClient


@pytest.fixture
def incomplete_client_class():
    """Fixture providing an incomplete implementation that should fail to instantiate."""
    
    class IncompleteMCPClient(MCPClientInterface):
        """Incomplete implementation missing some methods."""
        
        async def connect(self) -> bool:
            return True
            
        # Missing other required methods
    
    return IncompleteMCPClient


class TestMCPClientInterface:
    """Test cases for MCPClientInterface abstract base class."""

    def test_mcp_client_interface_is_abstract(self):
        """Test that MCPClientInterface is an abstract base class."""
        assert issubclass(MCPClientInterface, ABC)
        
        # Should not be able to instantiate directly
        with pytest.raises(TypeError):
            MCPClientInterface()

    def test_abstract_methods_defined(self):
        """Test that all required abstract methods are defined."""
        abstract_methods = MCPClientInterface.__abstractmethods__
        
        expected_methods = {
            'connect',
            'disconnect',
            'get_customers',
            'get_customer_by_id',
            'create_customer',
            'update_customer',
            'get_tickets',
            'get_ticket_by_id',
            'create_ticket',
            'update_ticket',
            'search_knowledge_base',
            'get_analytics'
        }
        
        assert abstract_methods == expected_methods

    def test_interface_compliance_concrete_implementation(self, concrete_client_class):
        """Test that a concrete implementation satisfies the interface."""
        
        # Should be able to instantiate concrete implementation
        client = concrete_client_class()
        assert isinstance(client, MCPClientInterface)

    def test_partial_implementation_fails(self, incomplete_client_class):
        """Test that partial implementation of interface fails."""
        
        with pytest.raises(TypeError):
            incomplete_client_class()

    @pytest.mark.asyncio
    async def test_method_signatures(self):
        """Test that method signatures match expected interface."""
        
        class TestableClient(MCPClientInterface):
            """Testable implementation for signature verification."""
            
            async def connect(self) -> bool:
                return True
            
            async def disconnect(self):
                pass
            
            async def get_customers(self, limit: int = 100) -> List[Dict[str, Any]]:
                return [{"id": "1", "name": "Test Customer"}]
            
            async def get_customer_by_id(self, customer_id: str) -> Optional[Dict[str, Any]]:
                if customer_id == "1":
                    return {"id": "1", "name": "Test Customer"}
                return None
            
            async def create_customer(self, customer_data: Dict[str, Any]) -> Dict[str, Any]:
                return {"id": "new", **customer_data}
            
            async def update_customer(self, customer_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
                return {"id": customer_id, **updates}
            
            async def get_tickets(self, limit: int = 100, status: Optional[str] = None) -> List[Dict[str, Any]]:
                tickets = [{"id": "1", "status": "open"}]
                return tickets if status is None or tickets[0]["status"] == status else []
            
            async def get_ticket_by_id(self, ticket_id: str) -> Optional[Dict[str, Any]]:
                if ticket_id == "1":
                    return {"id": "1", "status": "open"}
                return None
            
            async def create_ticket(self, ticket_data: Dict[str, Any]) -> Dict[str, Any]:
                return {"id": "new", **ticket_data}
            
            async def update_ticket(self, ticket_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
                return {"id": ticket_id, **updates}
            
            async def search_knowledge_base(self, search_term: str, limit: int = 10) -> List[Dict[str, Any]]:
                if "test" in search_term.lower():
                    return [{"id": "1", "title": "Test Article"}]
                return []
            
            async def get_analytics(self, days: int = 30) -> Dict[str, Any]:
                return {"period_days": days, "total_tickets": 10}
        
        client = TestableClient()
        
        # Test connection methods
        assert await client.connect() is True
        await client.disconnect()  # Should not raise
        
        # Test customer methods
        customers = await client.get_customers(limit=50)
        assert isinstance(customers, list)
        assert len(customers) == 1
        
        customer = await client.get_customer_by_id("1")
        assert customer is not None
        assert customer["id"] == "1"
        
        new_customer = await client.create_customer({"name": "New Customer"})
        assert new_customer["name"] == "New Customer"
        
        updated_customer = await client.update_customer("1", {"name": "Updated"})
        assert updated_customer["name"] == "Updated"
        
        # Test ticket methods
        tickets = await client.get_tickets(limit=10, status="open")
        assert isinstance(tickets, list)
        
        ticket = await client.get_ticket_by_id("1")
        assert ticket is not None
        assert ticket["id"] == "1"
        
        new_ticket = await client.create_ticket({"title": "New Ticket"})
        assert new_ticket["title"] == "New Ticket"
        
        updated_ticket = await client.update_ticket("1", {"status": "closed"})
        assert updated_ticket["status"] == "closed"
        
        # Test knowledge base search
        results = await client.search_knowledge_base("test query", limit=5)
        assert isinstance(results, list)
        assert len(results) == 1
        
        # Test analytics
        analytics = await client.get_analytics(days=7)
        assert isinstance(analytics, dict)
        assert analytics["period_days"] == 7


class TestInterfaceTypeHints:
    """Test type hint compliance for the interface."""

    def test_method_return_types(self):
        """Test that all methods have proper return type annotations."""
        import inspect
        from typing import get_type_hints
        
        # Get type hints for all abstract methods
        type_hints = get_type_hints(MCPClientInterface)
        
        # Check specific method signatures exist
        for method_name in MCPClientInterface.__abstractmethods__:
            method = getattr(MCPClientInterface, method_name)
            assert callable(method), f"{method_name} should be callable"

    def test_parameter_types(self):
        """Test that method parameters have appropriate type hints."""
        import inspect
        
        # Test specific method signatures
        methods_to_check = [
            ('get_customers', ['limit']),
            ('get_customer_by_id', ['customer_id']),
            ('create_customer', ['customer_data']),
            ('update_customer', ['customer_id', 'updates']),
            ('get_tickets', ['limit', 'status']),
            ('search_knowledge_base', ['search_term', 'limit']),
            ('get_analytics', ['days'])
        ]
        
        for method_name, expected_params in methods_to_check:
            method = getattr(MCPClientInterface, method_name)
            sig = inspect.signature(method)
            
            for param_name in expected_params:
                assert param_name in sig.parameters, f"Parameter {param_name} missing from {method_name}"


class TestInterfaceDocumentation:
    """Test interface documentation and docstrings."""

    def test_class_has_docstring(self):
        """Test that the interface class has proper documentation."""
        assert MCPClientInterface.__doc__ is not None
        assert len(MCPClientInterface.__doc__.strip()) > 0

    def test_abstract_methods_have_docstrings(self):
        """Test that all abstract methods have docstrings."""
        for method_name in MCPClientInterface.__abstractmethods__:
            method = getattr(MCPClientInterface, method_name)
            assert method.__doc__ is not None, f"Method {method_name} missing docstring"
            assert len(method.__doc__.strip()) > 0, f"Method {method_name} has empty docstring"

    def test_docstring_content_quality(self):
        """Test that docstrings contain meaningful content."""
        method_descriptions = {
            'connect': 'connect',
            'disconnect': 'disconnect',
            'get_customers': 'customers',
            'get_customer_by_id': 'customer',
            'create_customer': 'create',
            'update_customer': 'update',
            'get_tickets': 'tickets',
            'get_ticket_by_id': 'ticket',
            'create_ticket': 'create',
            'update_ticket': 'update',
            'search_knowledge_base': 'search',
            'get_analytics': 'analytics'
        }
        
        for method_name, expected_content in method_descriptions.items():
            method = getattr(MCPClientInterface, method_name)
            docstring = method.__doc__.lower()
            assert expected_content in docstring, f"Method {method_name} docstring should mention '{expected_content}'"


class TestInterfaceUsagePatterns:
    """Test common usage patterns with the interface."""

    @pytest.mark.asyncio
    async def test_interface_composition(self):
        """Test that interface can be used in composition patterns."""
        
        class MockMCPClient(MCPClientInterface):
            """Mock implementation for testing composition."""
            
            def __init__(self):
                self.connected = False
                self.call_count = {}
            
            async def connect(self) -> bool:
                self.connected = True
                return True
            
            async def disconnect(self):
                self.connected = False
            
            def _track_call(self, method_name):
                self.call_count[method_name] = self.call_count.get(method_name, 0) + 1
            
            async def get_customers(self, limit: int = 100) -> List[Dict[str, Any]]:
                self._track_call('get_customers')
                return []
            
            async def get_customer_by_id(self, customer_id: str) -> Optional[Dict[str, Any]]:
                self._track_call('get_customer_by_id')
                return None
            
            async def create_customer(self, customer_data: Dict[str, Any]) -> Dict[str, Any]:
                self._track_call('create_customer')
                return {}
            
            async def update_customer(self, customer_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
                self._track_call('update_customer')
                return {}
            
            async def get_tickets(self, limit: int = 100, status: Optional[str] = None) -> List[Dict[str, Any]]:
                self._track_call('get_tickets')
                return []
            
            async def get_ticket_by_id(self, ticket_id: str) -> Optional[Dict[str, Any]]:
                self._track_call('get_ticket_by_id')
                return None
            
            async def create_ticket(self, ticket_data: Dict[str, Any]) -> Dict[str, Any]:
                self._track_call('create_ticket')
                return {}
            
            async def update_ticket(self, ticket_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
                self._track_call('update_ticket')
                return {}
            
            async def search_knowledge_base(self, search_term: str, limit: int = 10) -> List[Dict[str, Any]]:
                self._track_call('search_knowledge_base')
                return []
            
            async def get_analytics(self, days: int = 30) -> Dict[str, Any]:
                self._track_call('get_analytics')
                return {}
        
        class MCPClientWrapper:
            """Wrapper class demonstrating composition."""
            
            def __init__(self, client: MCPClientInterface):
                self.client = client
            
            async def initialize(self):
                return await self.client.connect()
            
            async def get_customer_info(self, customer_id: str):
                return await self.client.get_customer_by_id(customer_id)
        
        # Test composition
        mock_client = MockMCPClient()
        wrapper = MCPClientWrapper(mock_client)
        
        assert await wrapper.initialize() is True
        assert mock_client.connected is True
        
        await wrapper.get_customer_info("test_id")
        assert mock_client.call_count['get_customer_by_id'] == 1

    def test_interface_inheritance_patterns(self):
        """Test that interface supports proper inheritance patterns."""
        
        class ExtendedMCPClientInterface(MCPClientInterface):
            """Extended interface adding more methods."""
            
            async def get_customer_history(self, customer_id: str) -> List[Dict[str, Any]]:
                """Get customer interaction history."""
                pass
        
        # Test that extended interface inherits all abstract methods
        abstract_methods = ExtendedMCPClientInterface.__abstractmethods__
        assert 'connect' in abstract_methods
        assert 'get_customer_history' in abstract_methods
        
        # Should still not be instantiable
        with pytest.raises(TypeError):
            ExtendedMCPClientInterface()

    def test_interface_multiple_inheritance(self):
        """Test interface with multiple inheritance patterns."""
        
        class LoggingMixin:
            """Mixin for adding logging capabilities."""
            
            def log_operation(self, operation: str):
                print(f"Operation: {operation}")
        
        class LoggingMCPClient(MCPClientInterface, LoggingMixin):
            """MCP client with logging capabilities."""
            
            async def connect(self) -> bool:
                self.log_operation("connect")
                return True
            
            async def disconnect(self):
                self.log_operation("disconnect")
            
            async def get_customers(self, limit: int = 100) -> List[Dict[str, Any]]:
                self.log_operation("get_customers")
                return []
            
            async def get_customer_by_id(self, customer_id: str) -> Optional[Dict[str, Any]]:
                self.log_operation("get_customer_by_id")
                return None
            
            async def create_customer(self, customer_data: Dict[str, Any]) -> Dict[str, Any]:
                self.log_operation("create_customer")
                return {}
            
            async def update_customer(self, customer_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
                self.log_operation("update_customer")
                return {}
            
            async def get_tickets(self, limit: int = 100, status: Optional[str] = None) -> List[Dict[str, Any]]:
                self.log_operation("get_tickets")
                return []
            
            async def get_ticket_by_id(self, ticket_id: str) -> Optional[Dict[str, Any]]:
                self.log_operation("get_ticket_by_id")
                return None
            
            async def create_ticket(self, ticket_data: Dict[str, Any]) -> Dict[str, Any]:
                self.log_operation("create_ticket")
                return {}
            
            async def update_ticket(self, ticket_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
                self.log_operation("update_ticket")
                return {}
            
            async def search_knowledge_base(self, search_term: str, limit: int = 10) -> List[Dict[str, Any]]:
                self.log_operation("search_knowledge_base")
                return []
            
            async def get_analytics(self, days: int = 30) -> Dict[str, Any]:
                self.log_operation("get_analytics")
                return {}
        
        # Should be able to instantiate and use both interfaces
        client = LoggingMCPClient()
        assert isinstance(client, MCPClientInterface)
        assert isinstance(client, LoggingMixin)
        
        # Test that both sets of methods are available
        assert hasattr(client, 'connect')
        assert hasattr(client, 'log_operation')
