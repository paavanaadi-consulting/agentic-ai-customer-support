"""
Comprehensive test suite for CustomerService.
Tests all customer-related business logic and data operations.
"""
import pytest
import uuid
from datetime import datetime
from unittest.mock import AsyncMock, Mock, patch
from typing import Dict, Any

from src.services.customer_service import CustomerService
from src.api.schemas import CustomerRequest, CustomerResponse
from src.mcp.postgres_mcp_client import OptimizedPostgreSQLMCPClient, MCPClientError


class TestCustomerService:
    """Test cases for CustomerService class."""

    @pytest.fixture
    def mock_mcp_client(self):
        """Create a mocked MCP client."""
        mock_client = AsyncMock(spec=OptimizedPostgreSQLMCPClient)
        return mock_client

    @pytest.fixture
    def customer_service(self):
        """Create a CustomerService instance with no MCP client (in-memory mode)."""
        return CustomerService()

    @pytest.fixture
    def customer_service_with_mcp(self, mock_mcp_client):
        """Create a CustomerService instance with mocked MCP client."""
        return CustomerService(mcp_client=mock_mcp_client)

    @pytest.fixture
    def sample_customer_request(self):
        """Create a sample customer request."""
        return CustomerRequest(
            name="John Doe",
            email="john.doe@example.com",
            phone="+1234567890",
            company="Test Company",
            metadata={"source": "web", "campaign": "spring2024"}
        )

    @pytest.fixture
    def sample_customer_data(self):
        """Create sample customer data for database responses."""
        return {
            "customer_id": "customer_123",
            "first_name": "John",
            "last_name": "Doe",
            "email": "john.doe@example.com",
            "phone": "+1234567890",
            "company": "Test Company",
            "created_at": datetime.utcnow(),
            "status": "active",
            "tier": "standard",
            "last_interaction": None
        }


class TestCustomerCreation:
    """Test customer creation functionality."""

    @pytest.mark.asyncio
    async def test_create_customer_in_memory_success(self, customer_service, sample_customer_request):
        """Test successful customer creation in memory mode."""
        with patch('src.services.customer_service.uuid.uuid4') as mock_uuid:
            mock_uuid.return_value.hex = "abcd1234" * 4
            expected_customer_id = str(mock_uuid.return_value)

            result = await customer_service.create_customer(sample_customer_request)

            assert isinstance(result, CustomerResponse)
            assert result.name == "John Doe"
            assert result.email == "john.doe@example.com"
            assert result.phone == "+1234567890"
            assert result.company == "Test Company"
            assert result.ticket_count == 0
            assert result.last_interaction is None
            assert result.status == "active"
            assert result.tier == "standard"
            assert result.metadata == {"source": "web", "campaign": "spring2024"}

    @pytest.mark.asyncio
    async def test_create_customer_with_mcp_success(self, customer_service_with_mcp, mock_mcp_client, 
                                                   sample_customer_request, sample_customer_data):
        """Test successful customer creation with MCP client."""
        mock_mcp_client.create_customer.return_value = sample_customer_data

        result = await customer_service_with_mcp.create_customer(sample_customer_request)

        assert isinstance(result, CustomerResponse)
        assert result.customer_id == "customer_123"
        assert result.name == "John Doe"
        assert result.email == "john.doe@example.com"
        mock_mcp_client.create_customer.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_customer_with_mcp_failure(self, customer_service_with_mcp, mock_mcp_client,
                                                   sample_customer_request):
        """Test customer creation failure with MCP client."""
        mock_mcp_client.create_customer.side_effect = MCPClientError("Database connection failed")

        with pytest.raises(Exception) as exc_info:
            await customer_service_with_mcp.create_customer(sample_customer_request)

        assert "Database error" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_create_customer_name_parsing(self, customer_service):
        """Test customer name parsing into first and last names."""
        # Single name
        request_single = CustomerRequest(name="John", email="john@test.com")
        result = await customer_service.create_customer(request_single)
        assert "John" in result.name
        
        # Multiple names
        request_multiple = CustomerRequest(name="John Michael Doe", email="john@test.com")
        result = await customer_service.create_customer(request_multiple)
        assert result.name == "John Michael Doe"

    @pytest.mark.asyncio
    async def test_create_customer_tier_determination(self, customer_service):
        """Test customer tier determination logic."""
        # Enterprise customer (has company)
        enterprise_request = CustomerRequest(
            name="Jane Smith",
            email="jane@enterprise.com",
            company="Enterprise Corp"
        )
        result = await customer_service.create_customer(enterprise_request)
        assert result.tier == "enterprise"
        
        # Standard customer (no company)
        standard_request = CustomerRequest(
            name="John Doe",
            email="john@personal.com"
        )
        result = await customer_service.create_customer(standard_request)
        assert result.tier == "standard"

    @pytest.mark.asyncio
    async def test_create_customer_validation(self, customer_service):
        """Test customer data validation."""
        # Invalid email
        with pytest.raises(ValueError):
            invalid_request = CustomerRequest(name="Test", email="invalid-email")
            await customer_service.create_customer(invalid_request)

    @pytest.mark.asyncio
    async def test_create_customer_welcome_sequence_triggered(self, customer_service_with_mcp, 
                                                             mock_mcp_client, sample_customer_request,
                                                             sample_customer_data):
        """Test that welcome sequence is triggered after customer creation."""
        mock_mcp_client.create_customer.return_value = sample_customer_data

        with patch.object(customer_service_with_mcp, '_trigger_welcome_sequence') as mock_welcome:
            await customer_service_with_mcp.create_customer(sample_customer_request)
            mock_welcome.assert_called_once()


class TestCustomerRetrieval:
    """Test customer retrieval functionality."""

    @pytest.mark.asyncio
    async def test_get_customer_by_id_memory_success(self, customer_service, sample_customer_request):
        """Test successful customer retrieval from memory."""
        # First create a customer
        created_customer = await customer_service.create_customer(sample_customer_request)
        
        # Then retrieve it
        result = await customer_service.get_customer_by_id(created_customer.customer_id)
        
        assert result is not None
        assert result.customer_id == created_customer.customer_id
        assert result.email == "john.doe@example.com"

    @pytest.mark.asyncio
    async def test_get_customer_by_id_memory_not_found(self, customer_service):
        """Test customer retrieval when customer doesn't exist in memory."""
        result = await customer_service.get_customer_by_id("nonexistent_id")
        assert result is None

    @pytest.mark.asyncio
    async def test_get_customer_by_id_mcp_success(self, customer_service_with_mcp, mock_mcp_client,
                                                 sample_customer_data):
        """Test successful customer retrieval with MCP client."""
        mock_mcp_client.get_customer_by_id.return_value = sample_customer_data

        result = await customer_service_with_mcp.get_customer_by_id("customer_123")

        assert result is not None
        assert result.customer_id == "customer_123"
        assert result.name == "John Doe"
        mock_mcp_client.get_customer_by_id.assert_called_once_with("customer_123")

    @pytest.mark.asyncio
    async def test_get_customer_by_id_mcp_not_found(self, customer_service_with_mcp, mock_mcp_client):
        """Test customer retrieval when customer doesn't exist with MCP client."""
        mock_mcp_client.get_customer_by_id.return_value = None

        result = await customer_service_with_mcp.get_customer_by_id("nonexistent_id")

        assert result is None

    @pytest.mark.asyncio
    async def test_get_customer_by_id_mcp_error_fallback(self, customer_service_with_mcp, mock_mcp_client,
                                                        sample_customer_request):
        """Test fallback to memory when MCP client fails."""
        mock_mcp_client.get_customer_by_id.side_effect = MCPClientError("Connection failed")

        # Add customer to memory storage
        created_customer = await customer_service_with_mcp.create_customer(sample_customer_request)
        customer_service_with_mcp.customers_db[created_customer.customer_id] = {
            "customer_id": created_customer.customer_id,
            "name": created_customer.name,
            "email": created_customer.email,
            "phone": created_customer.phone,
            "company": created_customer.company,
            "created_at": created_customer.created_at,
            "metadata": created_customer.metadata,
            "ticket_count": 0,
            "last_interaction": None,
            "status": "active",
            "tier": "standard"
        }

        result = await customer_service_with_mcp.get_customer_by_id(created_customer.customer_id)
        assert result is not None

    @pytest.mark.asyncio
    async def test_get_customer_by_email_success(self, customer_service, sample_customer_request):
        """Test successful customer retrieval by email."""
        created_customer = await customer_service.create_customer(sample_customer_request)
        
        result = await customer_service.get_customer_by_email("john.doe@example.com")
        
        assert result is not None
        assert result.email == "john.doe@example.com"
        assert result.customer_id == created_customer.customer_id

    @pytest.mark.asyncio
    async def test_get_customer_by_email_case_insensitive(self, customer_service, sample_customer_request):
        """Test case-insensitive email search."""
        await customer_service.create_customer(sample_customer_request)
        
        result = await customer_service.get_customer_by_email("JOHN.DOE@EXAMPLE.COM")
        
        assert result is not None
        assert result.email == "john.doe@example.com"

    @pytest.mark.asyncio
    async def test_get_customer_by_email_not_found(self, customer_service):
        """Test customer retrieval by email when not found."""
        result = await customer_service.get_customer_by_email("nonexistent@example.com")
        assert result is None


class TestCustomerUpdate:
    """Test customer update functionality."""

    @pytest.mark.asyncio
    async def test_update_customer_success(self, customer_service, sample_customer_request):
        """Test successful customer update."""
        created_customer = await customer_service.create_customer(sample_customer_request)
        
        updates = {
            "name": "John Smith",
            "phone": "+9876543210",
            "company": "New Company"
        }
        
        result = await customer_service.update_customer(created_customer.customer_id, updates)
        
        assert result is not None
        assert result.name == "John Smith"
        assert result.phone == "+9876543210"
        assert result.company == "New Company"
        assert result.email == "john.doe@example.com"  # Unchanged

    @pytest.mark.asyncio
    async def test_update_customer_not_found(self, customer_service):
        """Test customer update when customer doesn't exist."""
        updates = {"name": "New Name"}
        result = await customer_service.update_customer("nonexistent_id", updates)
        assert result is None

    @pytest.mark.asyncio
    async def test_update_customer_invalid_field(self, customer_service, sample_customer_request):
        """Test customer update with invalid field."""
        created_customer = await customer_service.create_customer(sample_customer_request)
        
        updates = {"invalid_field": "value"}
        
        with pytest.raises(ValueError) as exc_info:
            await customer_service.update_customer(created_customer.customer_id, updates)
        
        assert "cannot be updated" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_update_last_interaction(self, customer_service, sample_customer_request):
        """Test updating last interaction timestamp."""
        created_customer = await customer_service.create_customer(sample_customer_request)
        
        await customer_service.update_last_interaction(created_customer.customer_id)
        
        # Verify in memory storage
        stored_customer = customer_service.customers_db[created_customer.customer_id]
        assert stored_customer["last_interaction"] is not None
        assert isinstance(stored_customer["last_interaction"], datetime)

    @pytest.mark.asyncio
    async def test_update_last_interaction_mcp(self, customer_service_with_mcp, mock_mcp_client):
        """Test updating last interaction with MCP client."""
        await customer_service_with_mcp.update_last_interaction("customer_123")
        
        mock_mcp_client.update_customer.assert_called_once()
        call_args = mock_mcp_client.update_customer.call_args
        assert call_args[0][0] == "customer_123"
        assert "last_interaction" in call_args[0][1]

    @pytest.mark.asyncio
    async def test_increment_ticket_count(self, customer_service, sample_customer_request):
        """Test incrementing customer ticket count."""
        created_customer = await customer_service.create_customer(sample_customer_request)
        
        await customer_service.increment_ticket_count(created_customer.customer_id)
        
        stored_customer = customer_service.customers_db[created_customer.customer_id]
        assert stored_customer["ticket_count"] == 1
        
        # Increment again
        await customer_service.increment_ticket_count(created_customer.customer_id)
        stored_customer = customer_service.customers_db[created_customer.customer_id]
        assert stored_customer["ticket_count"] == 2


class TestCustomerListing:
    """Test customer listing functionality."""

    @pytest.mark.asyncio
    async def test_list_customers_memory(self, customer_service):
        """Test listing customers from memory."""
        # Create multiple customers
        requests = [
            CustomerRequest(name="John Doe", email="john@test.com"),
            CustomerRequest(name="Jane Smith", email="jane@test.com"),
            CustomerRequest(name="Bob Johnson", email="bob@test.com")
        ]
        
        for request in requests:
            await customer_service.create_customer(request)
        
        result = await customer_service.list_customers()
        
        assert len(result) == 3
        assert all(isinstance(customer, CustomerResponse) for customer in result)
        emails = [customer.email for customer in result]
        assert "john@test.com" in emails
        assert "jane@test.com" in emails
        assert "bob@test.com" in emails

    @pytest.mark.asyncio
    async def test_list_customers_with_limit(self, customer_service):
        """Test listing customers with limit."""
        # Create multiple customers
        for i in range(5):
            request = CustomerRequest(name=f"Customer {i}", email=f"customer{i}@test.com")
            await customer_service.create_customer(request)
        
        result = await customer_service.list_customers(limit=3)
        
        assert len(result) == 3

    @pytest.mark.asyncio
    async def test_list_customers_mcp(self, customer_service_with_mcp, mock_mcp_client):
        """Test listing customers with MCP client."""
        sample_customers = [
            {
                "customer_id": "customer_1",
                "first_name": "John",
                "last_name": "Doe",
                "email": "john@test.com",
                "phone": None,
                "company": None,
                "created_at": datetime.utcnow(),
                "status": "active",
                "tier": "standard",
                "last_interaction": None
            },
            {
                "customer_id": "customer_2",
                "first_name": "Jane",
                "last_name": "Smith",
                "email": "jane@test.com",
                "phone": None,
                "company": None,
                "created_at": datetime.utcnow(),
                "status": "active",
                "tier": "standard",
                "last_interaction": None
            }
        ]
        
        mock_mcp_client.get_customers.return_value = sample_customers
        
        result = await customer_service_with_mcp.list_customers()
        
        assert len(result) == 2
        assert result[0].name == "John Doe"
        assert result[1].name == "Jane Smith"
        mock_mcp_client.get_customers.assert_called_once_with(limit=100)

    @pytest.mark.asyncio
    async def test_list_customers_empty(self, customer_service):
        """Test listing customers when none exist."""
        result = await customer_service.list_customers()
        assert result == []


class TestCustomerAnalytics:
    """Test customer analytics functionality."""

    @pytest.mark.asyncio
    async def test_get_customer_count(self, customer_service):
        """Test getting customer count."""
        # Initially should be 0
        assert customer_service.get_customer_count() == 0
        
        # Create customers
        for i in range(3):
            request = CustomerRequest(name=f"Customer {i}", email=f"customer{i}@test.com")
            await customer_service.create_customer(request)
        
        assert customer_service.get_customer_count() == 3

    @pytest.mark.asyncio
    async def test_get_customers_by_tier(self, customer_service):
        """Test getting customers grouped by tier."""
        # Create customers with different tiers
        standard_request = CustomerRequest(name="Standard User", email="standard@test.com")
        enterprise_request = CustomerRequest(
            name="Enterprise User", 
            email="enterprise@test.com",
            company="Enterprise Corp"
        )
        
        await customer_service.create_customer(standard_request)
        await customer_service.create_customer(enterprise_request)
        
        result = customer_service.get_customers_by_tier()
        
        assert "standard" in result
        assert "enterprise" in result
        assert result["standard"] == 1
        assert result["enterprise"] == 1


class TestCustomerValidation:
    """Test customer data validation."""

    def test_validate_customer_data_valid_email(self, customer_service):
        """Test validation with valid email."""
        request = CustomerRequest(name="John Doe", email="valid@example.com")
        # Should not raise any exception
        customer_service._validate_customer_data(request)

    def test_validate_customer_data_invalid_email(self, customer_service):
        """Test validation with invalid email."""
        request = CustomerRequest(name="John Doe", email="invalid-email")
        
        with pytest.raises(ValueError) as exc_info:
            customer_service._validate_customer_data(request)
        
        assert "Invalid email format" in str(exc_info.value)

    def test_validate_customer_data_empty_name(self, customer_service):
        """Test validation with empty name."""
        request = CustomerRequest(name="", email="valid@example.com")
        
        with pytest.raises(ValueError) as exc_info:
            customer_service._validate_customer_data(request)
        
        assert "Name cannot be empty" in str(exc_info.value)


class TestCustomerServiceHelpers:
    """Test helper methods in CustomerService."""

    def test_determine_customer_tier_standard(self, customer_service):
        """Test tier determination for standard customer."""
        request = CustomerRequest(name="John Doe", email="john@personal.com")
        tier = customer_service._determine_customer_tier(request)
        assert tier == "standard"

    def test_determine_customer_tier_enterprise(self, customer_service):
        """Test tier determination for enterprise customer."""
        request = CustomerRequest(
            name="Jane Smith", 
            email="jane@company.com",
            company="Big Corporation"
        )
        tier = customer_service._determine_customer_tier(request)
        assert tier == "enterprise"

    @pytest.mark.asyncio
    async def test_trigger_welcome_sequence(self, customer_service):
        """Test welcome sequence triggering."""
        with patch('asyncio.sleep') as mock_sleep:
            await customer_service._trigger_welcome_sequence("customer_123")
            # Should complete without errors
            mock_sleep.assert_called()


class TestCustomerServiceIntegration:
    """Test integration scenarios for CustomerService."""

    @pytest.mark.asyncio
    async def test_full_customer_lifecycle(self, customer_service):
        """Test complete customer lifecycle."""
        # Create customer
        request = CustomerRequest(
            name="Lifecycle Customer",
            email="lifecycle@test.com",
            company="Test Company"
        )
        
        created = await customer_service.create_customer(request)
        assert created is not None
        assert created.ticket_count == 0
        
        # Update last interaction
        await customer_service.update_last_interaction(created.customer_id)
        
        # Increment ticket count
        await customer_service.increment_ticket_count(created.customer_id)
        
        # Update customer info
        updates = {"company": "Updated Company"}
        updated = await customer_service.update_customer(created.customer_id, updates)
        assert updated.company == "Updated Company"
        
        # Retrieve final state
        final = await customer_service.get_customer_by_id(created.customer_id)
        assert final is not None
        assert final.company == "Updated Company"

    @pytest.mark.asyncio
    async def test_concurrent_customer_operations(self, customer_service):
        """Test concurrent customer operations."""
        import asyncio
        
        async def create_customer(index):
            request = CustomerRequest(
                name=f"Concurrent Customer {index}",
                email=f"concurrent{index}@test.com"
            )
            return await customer_service.create_customer(request)
        
        # Create multiple customers concurrently
        tasks = [create_customer(i) for i in range(5)]
        results = await asyncio.gather(*tasks)
        
        assert len(results) == 5
        assert len(set(r.customer_id for r in results)) == 5  # All unique IDs

    @pytest.mark.asyncio
    async def test_error_handling_chain(self, customer_service_with_mcp, mock_mcp_client):
        """Test error handling with MCP client failures."""
        # Setup MCP client to fail on create but succeed on fallback operations
        mock_mcp_client.create_customer.side_effect = MCPClientError("Create failed")
        
        request = CustomerRequest(name="Error Test", email="error@test.com")
        
        with pytest.raises(Exception) as exc_info:
            await customer_service_with_mcp.create_customer(request)
        
        assert "Database error" in str(exc_info.value)


class TestCustomerServiceMocking:
    """Test CustomerService with various mocking scenarios."""

    @pytest.mark.asyncio
    async def test_mcp_client_none_handling(self):
        """Test service behavior when MCP client is None."""
        service = CustomerService(mcp_client=None)
        request = CustomerRequest(name="Test User", email="test@example.com")
        
        result = await service.create_customer(request)
        assert result is not None
        assert result.name == "Test User"

    @pytest.mark.asyncio
    async def test_partial_mcp_failure_recovery(self, customer_service_with_mcp, mock_mcp_client,
                                               sample_customer_request):
        """Test recovery from partial MCP failures."""
        # First call fails, second succeeds
        mock_mcp_client.create_customer.side_effect = [
            MCPClientError("Temporary failure"),
            None  # Success on retry wouldn't happen in current implementation
        ]
        
        with pytest.raises(Exception):
            await customer_service_with_mcp.create_customer(sample_customer_request)
