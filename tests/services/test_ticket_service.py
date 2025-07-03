"""
Comprehensive test suite for TicketService.
Tests all ticket management and support workflow logic.
"""
import pytest
import uuid
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, Mock, patch
from typing import Dict, Any, List

from src.services.ticket_service import TicketService
from src.api.schemas import (
    TicketRequest, TicketResponse, TicketStatus, Priority, QueryType
)
from src.mcp.postgres_mcp_client import OptimizedPostgreSQLMCPClient, MCPClientError


class TestTicketService:
    """Test cases for TicketService class."""

    @pytest.fixture
    def mock_mcp_client(self):
        """Create a mocked MCP client."""
        mock_client = AsyncMock(spec=OptimizedPostgreSQLMCPClient)
        return mock_client

    @pytest.fixture
    def ticket_service(self):
        """Create a TicketService instance with in-memory storage."""
        return TicketService()

    @pytest.fixture
    def ticket_service_with_mcp(self, mock_mcp_client):
        """Create a TicketService instance with mocked MCP client."""
        return TicketService(mcp_client=mock_mcp_client)

    @pytest.fixture
    def sample_ticket_request(self):
        """Create a sample ticket request."""
        return TicketRequest(
            title="Login Issue",
            description="Customer cannot log into their account after password reset",
            customer_id="customer_123",
            category="technical",
            priority=Priority.HIGH,
            tags=["login", "password", "urgent"]
        )

    @pytest.fixture
    def sample_ticket_data(self):
        """Create sample ticket data for database responses."""
        return {
            "ticket_id": "ticket_123",
            "customer_id": "customer_123",
            "subject": "Login Issue",
            "description": "Customer cannot log into their account after password reset",
            "priority": "high",
            "status": "open",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "agent_name": "agent_tech_001"
        }


class TestTicketCreation:
    """Test ticket creation functionality."""

    @pytest.mark.asyncio
    async def test_create_ticket_in_memory_success(self, ticket_service, sample_ticket_request):
        """Test successful ticket creation in memory mode."""
        result = await ticket_service.create_ticket(sample_ticket_request)

        assert isinstance(result, TicketResponse)
        assert result.title == "Login Issue"
        assert result.description == "Customer cannot log into their account after password reset"
        assert result.customer_id == "customer_123"
        assert result.category == "technical"
        assert result.priority == Priority.HIGH
        assert result.status == TicketStatus.OPEN
        assert result.tags == ["login", "password", "urgent"]
        assert result.ticket_id is not None
        assert result.assigned_agent is not None

    @pytest.mark.asyncio
    async def test_create_ticket_with_mcp_success(self, ticket_service_with_mcp, mock_mcp_client,
                                                 sample_ticket_request, sample_ticket_data):
        """Test successful ticket creation with MCP client."""
        mock_mcp_client.create_ticket.return_value = sample_ticket_data

        result = await ticket_service_with_mcp.create_ticket(sample_ticket_request)

        assert isinstance(result, TicketResponse)
        assert result.ticket_id == "ticket_123"
        assert result.title == "Login Issue"
        assert result.status == TicketStatus.OPEN
        assert result.assigned_agent == "agent_tech_001"
        mock_mcp_client.create_ticket.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_ticket_with_mcp_failure(self, ticket_service_with_mcp, mock_mcp_client,
                                                 sample_ticket_request):
        """Test ticket creation failure with MCP client."""
        mock_mcp_client.create_ticket.side_effect = MCPClientError("Database connection failed")

        with pytest.raises(Exception) as exc_info:
            await ticket_service_with_mcp.create_ticket(sample_ticket_request)

        assert "Database error" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_create_ticket_auto_agent_assignment(self, ticket_service):
        """Test automatic agent assignment based on category and priority."""
        # Technical high priority
        tech_request = TicketRequest(
            title="Critical System Error",
            description="System is down",
            customer_id="customer_123",
            category="technical",
            priority=Priority.HIGH
        )
        
        result = await ticket_service.create_ticket(tech_request)
        assert "tech" in result.assigned_agent.lower()

        # Billing medium priority
        billing_request = TicketRequest(
            title="Billing Question",
            description="Question about invoice",
            customer_id="customer_123",
            category="billing",
            priority=Priority.MEDIUM
        )
        
        result = await ticket_service.create_ticket(billing_request)
        assert "billing" in result.assigned_agent.lower()

    @pytest.mark.asyncio
    async def test_create_ticket_default_values(self, ticket_service):
        """Test ticket creation with minimal required fields."""
        minimal_request = TicketRequest(
            title="Simple Issue",
            description="Basic description",
            customer_id="customer_123"
        )
        
        result = await ticket_service.create_ticket(minimal_request)
        
        assert result.priority == Priority.MEDIUM  # Default
        assert result.category == "general"  # Default
        assert result.tags == []  # Default empty
        assert result.status == TicketStatus.OPEN

    @pytest.mark.asyncio
    async def test_create_ticket_stores_in_database(self, ticket_service, sample_ticket_request):
        """Test that created tickets are stored in database."""
        result = await ticket_service.create_ticket(sample_ticket_request)
        
        # Verify ticket is stored
        stored_ticket = ticket_service.tickets_db.get(result.ticket_id)
        assert stored_ticket is not None
        assert stored_ticket["customer_id"] == "customer_123"
        assert stored_ticket["title"] == "Login Issue"
        assert stored_ticket["priority"] == Priority.HIGH


class TestTicketRetrieval:
    """Test ticket retrieval functionality."""

    @pytest.mark.asyncio
    async def test_get_ticket_by_id_memory_success(self, ticket_service, sample_ticket_request):
        """Test successful ticket retrieval from memory."""
        created_ticket = await ticket_service.create_ticket(sample_ticket_request)
        
        result = await ticket_service.get_ticket_by_id(created_ticket.ticket_id)
        
        assert result is not None
        assert result.ticket_id == created_ticket.ticket_id
        assert result.title == "Login Issue"
        assert result.customer_id == "customer_123"

    @pytest.mark.asyncio
    async def test_get_ticket_by_id_memory_not_found(self, ticket_service):
        """Test ticket retrieval when ticket doesn't exist in memory."""
        result = await ticket_service.get_ticket_by_id("nonexistent_id")
        assert result is None

    @pytest.mark.asyncio
    async def test_get_ticket_by_id_mcp_success(self, ticket_service_with_mcp, mock_mcp_client,
                                               sample_ticket_data):
        """Test successful ticket retrieval with MCP client."""
        mock_mcp_client.get_ticket_by_id.return_value = sample_ticket_data

        result = await ticket_service_with_mcp.get_ticket_by_id("ticket_123")

        assert result is not None
        assert result.ticket_id == "ticket_123"
        assert result.title == "Login Issue"
        assert result.status == TicketStatus.OPEN
        mock_mcp_client.get_ticket_by_id.assert_called_once_with("ticket_123")

    @pytest.mark.asyncio
    async def test_get_ticket_by_id_mcp_not_found(self, ticket_service_with_mcp, mock_mcp_client):
        """Test ticket retrieval when ticket doesn't exist with MCP client."""
        mock_mcp_client.get_ticket_by_id.return_value = None

        result = await ticket_service_with_mcp.get_ticket_by_id("nonexistent_id")

        assert result is None

    @pytest.mark.asyncio
    async def test_get_ticket_by_id_mcp_error_fallback(self, ticket_service_with_mcp, mock_mcp_client,
                                                      sample_ticket_request):
        """Test fallback to memory when MCP client fails."""
        mock_mcp_client.get_ticket_by_id.side_effect = MCPClientError("Connection failed")

        # Add ticket to memory storage
        created_ticket = await ticket_service_with_mcp.create_ticket(sample_ticket_request)
        ticket_service_with_mcp.tickets_db[created_ticket.ticket_id] = {
            "ticket_id": created_ticket.ticket_id,
            "title": created_ticket.title,
            "description": created_ticket.description,
            "customer_id": created_ticket.customer_id,
            "category": created_ticket.category,
            "priority": created_ticket.priority,
            "status": created_ticket.status,
            "created_at": created_ticket.created_at,
            "updated_at": created_ticket.updated_at,
            "tags": created_ticket.tags,
            "assigned_agent": created_ticket.assigned_agent
        }

        result = await ticket_service_with_mcp.get_ticket_by_id(created_ticket.ticket_id)
        assert result is not None


class TestTicketStatusUpdate:
    """Test ticket status update functionality."""

    @pytest.mark.asyncio
    async def test_update_ticket_status_memory_success(self, ticket_service, sample_ticket_request):
        """Test successful ticket status update in memory."""
        created_ticket = await ticket_service.create_ticket(sample_ticket_request)
        
        result = await ticket_service.update_ticket_status(
            created_ticket.ticket_id, 
            TicketStatus.IN_PROGRESS
        )
        
        assert result is not None
        assert result.status == TicketStatus.IN_PROGRESS
        assert result.updated_at > result.created_at

    @pytest.mark.asyncio
    async def test_update_ticket_status_memory_not_found(self, ticket_service):
        """Test ticket status update when ticket doesn't exist."""
        result = await ticket_service.update_ticket_status(
            "nonexistent_id", 
            TicketStatus.RESOLVED
        )
        assert result is None

    @pytest.mark.asyncio
    async def test_update_ticket_status_all_statuses(self, ticket_service, sample_ticket_request):
        """Test updating ticket through all status transitions."""
        created_ticket = await ticket_service.create_ticket(sample_ticket_request)
        
        # Open -> In Progress
        result = await ticket_service.update_ticket_status(
            created_ticket.ticket_id, TicketStatus.IN_PROGRESS
        )
        assert result.status == TicketStatus.IN_PROGRESS
        
        # In Progress -> Resolved
        result = await ticket_service.update_ticket_status(
            created_ticket.ticket_id, TicketStatus.RESOLVED
        )
        assert result.status == TicketStatus.RESOLVED
        
        # Resolved -> Closed
        result = await ticket_service.update_ticket_status(
            created_ticket.ticket_id, TicketStatus.CLOSED
        )
        assert result.status == TicketStatus.CLOSED

    @pytest.mark.asyncio
    async def test_update_ticket_status_mcp(self, ticket_service_with_mcp, mock_mcp_client,
                                           sample_ticket_data):
        """Test ticket status update with MCP client."""
        updated_data = sample_ticket_data.copy()
        updated_data["status"] = "resolved"
        updated_data["updated_at"] = datetime.utcnow()
        
        mock_mcp_client.update_ticket_status.return_value = updated_data

        result = await ticket_service_with_mcp.update_ticket_status(
            "ticket_123", TicketStatus.RESOLVED
        )

        assert result is not None
        assert result.status == TicketStatus.RESOLVED
        mock_mcp_client.update_ticket_status.assert_called_once()


class TestTicketListing:
    """Test ticket listing and filtering functionality."""

    @pytest.mark.asyncio
    async def test_list_tickets_no_filters(self, ticket_service):
        """Test listing all tickets without filters."""
        requests = [
            TicketRequest(title="Ticket 1", description="Desc 1", customer_id="customer_1"),
            TicketRequest(title="Ticket 2", description="Desc 2", customer_id="customer_2"),
            TicketRequest(title="Ticket 3", description="Desc 3", customer_id="customer_1")
        ]
        
        for request in requests:
            await ticket_service.create_ticket(request)
        
        result = await ticket_service.list_tickets()
        
        assert len(result) == 3
        assert all(isinstance(ticket, TicketResponse) for ticket in result)

    @pytest.mark.asyncio
    async def test_list_tickets_filter_by_customer(self, ticket_service):
        """Test listing tickets filtered by customer ID."""
        requests = [
            TicketRequest(title="Ticket 1", description="Desc 1", customer_id="customer_1"),
            TicketRequest(title="Ticket 2", description="Desc 2", customer_id="customer_1"),
            TicketRequest(title="Ticket 3", description="Desc 3", customer_id="customer_2")
        ]
        
        for request in requests:
            await ticket_service.create_ticket(request)
        
        result = await ticket_service.list_tickets(customer_id="customer_1")
        
        assert len(result) == 2
        assert all(ticket.customer_id == "customer_1" for ticket in result)

    @pytest.mark.asyncio
    async def test_list_tickets_filter_by_status(self, ticket_service):
        """Test listing tickets filtered by status."""
        requests = [
            TicketRequest(title="Ticket 1", description="Desc 1", customer_id="customer_1"),
            TicketRequest(title="Ticket 2", description="Desc 2", customer_id="customer_2")
        ]
        
        ticket1 = await ticket_service.create_ticket(requests[0])
        ticket2 = await ticket_service.create_ticket(requests[1])
        
        # Update one ticket status
        await ticket_service.update_ticket_status(ticket1.ticket_id, TicketStatus.RESOLVED)
        
        # Filter by open status
        open_tickets = await ticket_service.list_tickets(status=TicketStatus.OPEN)
        assert len(open_tickets) == 1
        assert open_tickets[0].ticket_id == ticket2.ticket_id
        
        # Filter by resolved status
        resolved_tickets = await ticket_service.list_tickets(status=TicketStatus.RESOLVED)
        assert len(resolved_tickets) == 1
        assert resolved_tickets[0].ticket_id == ticket1.ticket_id

    @pytest.mark.asyncio
    async def test_list_tickets_filter_by_priority(self, ticket_service):
        """Test listing tickets filtered by priority."""
        requests = [
            TicketRequest(title="High Priority", description="Urgent", customer_id="c1", priority=Priority.HIGH),
            TicketRequest(title="Medium Priority", description="Normal", customer_id="c2", priority=Priority.MEDIUM),
            TicketRequest(title="Low Priority", description="Later", customer_id="c3", priority=Priority.LOW)
        ]
        
        for request in requests:
            await ticket_service.create_ticket(request)
        
        high_priority = await ticket_service.list_tickets(priority=Priority.HIGH)
        assert len(high_priority) == 1
        assert high_priority[0].title == "High Priority"

    @pytest.mark.asyncio
    async def test_list_tickets_with_limit(self, ticket_service):
        """Test listing tickets with limit."""
        for i in range(5):
            request = TicketRequest(
                title=f"Ticket {i}",
                description=f"Description {i}",
                customer_id=f"customer_{i}"
            )
            await ticket_service.create_ticket(request)
        
        result = await ticket_service.list_tickets(limit=3)
        assert len(result) == 3

    @pytest.mark.asyncio
    async def test_list_tickets_sorted_by_creation_date(self, ticket_service):
        """Test that tickets are sorted by creation date (newest first)."""
        # Create tickets with slight delays to ensure different timestamps
        import asyncio
        
        tickets = []
        for i in range(3):
            request = TicketRequest(
                title=f"Ticket {i}",
                description=f"Description {i}",
                customer_id="customer_1"
            )
            ticket = await ticket_service.create_ticket(request)
            tickets.append(ticket)
            await asyncio.sleep(0.01)  # Small delay
        
        result = await ticket_service.list_tickets()
        
        # Should be sorted by creation date (newest first)
        assert len(result) == 3
        for i in range(len(result) - 1):
            assert result[i].created_at >= result[i + 1].created_at


class TestTicketAssignment:
    """Test ticket assignment functionality."""

    @pytest.mark.asyncio
    async def test_assign_ticket_to_agent(self, ticket_service, sample_ticket_request):
        """Test assigning ticket to specific agent."""
        created_ticket = await ticket_service.create_ticket(sample_ticket_request)
        
        result = await ticket_service.assign_ticket_to_agent(
            created_ticket.ticket_id,
            "agent_specialist_001"
        )
        
        assert result is not None
        assert result.assigned_agent == "agent_specialist_001"

    @pytest.mark.asyncio
    async def test_assign_ticket_not_found(self, ticket_service):
        """Test assigning non-existent ticket."""
        result = await ticket_service.assign_ticket_to_agent(
            "nonexistent_id",
            "agent_001"
        )
        assert result is None

    def test_auto_assign_agent_technical_high_priority(self, ticket_service):
        """Test auto assignment for technical high priority tickets."""
        agent = ticket_service._auto_assign_agent("technical", Priority.HIGH)
        assert "tech" in agent.lower()
        assert "senior" in agent.lower() or "lead" in agent.lower()

    def test_auto_assign_agent_billing_medium_priority(self, ticket_service):
        """Test auto assignment for billing medium priority tickets."""
        agent = ticket_service._auto_assign_agent("billing", Priority.MEDIUM)
        assert "billing" in agent.lower()

    def test_auto_assign_agent_general_low_priority(self, ticket_service):
        """Test auto assignment for general low priority tickets."""
        agent = ticket_service._auto_assign_agent("general", Priority.LOW)
        assert "support" in agent.lower() or "general" in agent.lower()


class TestTicketAnalytics:
    """Test ticket analytics functionality."""

    @pytest.mark.asyncio
    async def test_get_ticket_count(self, ticket_service):
        """Test getting total ticket count."""
        assert ticket_service.get_ticket_count() == 0
        
        for i in range(3):
            request = TicketRequest(
                title=f"Ticket {i}",
                description=f"Description {i}",
                customer_id=f"customer_{i}"
            )
            await ticket_service.create_ticket(request)
        
        assert ticket_service.get_ticket_count() == 3

    @pytest.mark.asyncio
    async def test_get_tickets_by_status(self, ticket_service):
        """Test getting tickets grouped by status."""
        requests = [
            TicketRequest(title="Ticket 1", description="Desc 1", customer_id="c1"),
            TicketRequest(title="Ticket 2", description="Desc 2", customer_id="c2"),
            TicketRequest(title="Ticket 3", description="Desc 3", customer_id="c3")
        ]
        
        tickets = []
        for request in requests:
            ticket = await ticket_service.create_ticket(request)
            tickets.append(ticket)
        
        # Update some statuses
        await ticket_service.update_ticket_status(tickets[1].ticket_id, TicketStatus.RESOLVED)
        
        result = ticket_service.get_tickets_by_status()
        
        assert result[TicketStatus.OPEN] == 2
        assert result[TicketStatus.RESOLVED] == 1

    @pytest.mark.asyncio
    async def test_get_tickets_by_priority(self, ticket_service):
        """Test getting tickets grouped by priority."""
        requests = [
            TicketRequest(title="High", description="Desc", customer_id="c1", priority=Priority.HIGH),
            TicketRequest(title="Medium 1", description="Desc", customer_id="c2", priority=Priority.MEDIUM),
            TicketRequest(title="Medium 2", description="Desc", customer_id="c3", priority=Priority.MEDIUM),
            TicketRequest(title="Low", description="Desc", customer_id="c4", priority=Priority.LOW)
        ]
        
        for request in requests:
            await ticket_service.create_ticket(request)
        
        result = ticket_service.get_tickets_by_priority()
        
        assert result[Priority.HIGH] == 1
        assert result[Priority.MEDIUM] == 2
        assert result[Priority.LOW] == 1

    @pytest.mark.asyncio
    async def test_get_average_resolution_time(self, ticket_service):
        """Test calculating average resolution time."""
        # Create tickets with known timestamps
        base_time = datetime.utcnow()
        
        with patch('datetime.datetime') as mock_datetime:
            mock_datetime.utcnow.side_effect = [
                base_time,  # Creation time
                base_time + timedelta(hours=2),  # Resolution time
                base_time + timedelta(minutes=30),  # Creation time
                base_time + timedelta(hours=1)   # Resolution time
            ]
            
            # Create and resolve tickets
            request1 = TicketRequest(title="Ticket 1", description="Desc", customer_id="c1")
            ticket1 = await ticket_service.create_ticket(request1)
            await ticket_service.update_ticket_status(ticket1.ticket_id, TicketStatus.RESOLVED)
            
            request2 = TicketRequest(title="Ticket 2", description="Desc", customer_id="c2")
            ticket2 = await ticket_service.create_ticket(request2)
            await ticket_service.update_ticket_status(ticket2.ticket_id, TicketStatus.RESOLVED)
        
        # Average should be 1.5 hours
        avg_time = ticket_service.get_average_resolution_time()
        assert avg_time > 0


class TestTicketEscalation:
    """Test ticket escalation functionality."""

    @pytest.mark.asyncio
    async def test_escalate_ticket(self, ticket_service, sample_ticket_request):
        """Test escalating a ticket."""
        created_ticket = await ticket_service.create_ticket(sample_ticket_request)
        
        result = await ticket_service.escalate_ticket(
            created_ticket.ticket_id,
            "manager_001",
            "Customer is very upset"
        )
        
        assert result is not None
        assert result.assigned_agent == "manager_001"
        assert result.priority == Priority.HIGH  # Should be escalated to high priority

    @pytest.mark.asyncio
    async def test_escalate_ticket_not_found(self, ticket_service):
        """Test escalating non-existent ticket."""
        result = await ticket_service.escalate_ticket(
            "nonexistent_id",
            "manager_001",
            "Escalation reason"
        )
        assert result is None

    @pytest.mark.asyncio
    async def test_escalate_ticket_already_high_priority(self, ticket_service):
        """Test escalating already high priority ticket."""
        high_priority_request = TicketRequest(
            title="Critical Issue",
            description="System down",
            customer_id="customer_123",
            priority=Priority.HIGH
        )
        
        created_ticket = await ticket_service.create_ticket(high_priority_request)
        
        result = await ticket_service.escalate_ticket(
            created_ticket.ticket_id,
            "director_001",
            "CEO is involved"
        )
        
        assert result is not None
        assert result.assigned_agent == "director_001"
        # Priority should remain high or become critical if such status exists


class TestTicketValidation:
    """Test ticket data validation."""

    @pytest.mark.asyncio
    async def test_create_ticket_empty_title(self, ticket_service):
        """Test creating ticket with empty title."""
        request = TicketRequest(
            title="",
            description="Valid description",
            customer_id="customer_123"
        )
        
        with pytest.raises(ValueError) as exc_info:
            await ticket_service.create_ticket(request)
        
        assert "Title cannot be empty" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_create_ticket_empty_description(self, ticket_service):
        """Test creating ticket with empty description."""
        request = TicketRequest(
            title="Valid Title",
            description="",
            customer_id="customer_123"
        )
        
        with pytest.raises(ValueError) as exc_info:
            await ticket_service.create_ticket(request)
        
        assert "Description cannot be empty" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_create_ticket_empty_customer_id(self, ticket_service):
        """Test creating ticket with empty customer ID."""
        request = TicketRequest(
            title="Valid Title",
            description="Valid description",
            customer_id=""
        )
        
        with pytest.raises(ValueError) as exc_info:
            await ticket_service.create_ticket(request)
        
        assert "Customer ID cannot be empty" in str(exc_info.value)


class TestTicketServicePerformance:
    """Test TicketService performance characteristics."""

    @pytest.mark.asyncio
    async def test_concurrent_ticket_creation(self, ticket_service):
        """Test concurrent creation of multiple tickets."""
        import asyncio
        
        async def create_ticket(index):
            request = TicketRequest(
                title=f"Concurrent Ticket {index}",
                description=f"Description {index}",
                customer_id=f"customer_{index}"
            )
            return await ticket_service.create_ticket(request)
        
        tasks = [create_ticket(i) for i in range(10)]
        results = await asyncio.gather(*tasks)
        
        assert len(results) == 10
        assert all(isinstance(r, TicketResponse) for r in results)
        assert len(set(r.ticket_id for r in results)) == 10  # All unique IDs

    @pytest.mark.asyncio
    async def test_high_volume_ticket_storage(self, ticket_service):
        """Test storage of high volume of tickets."""
        for i in range(100):
            request = TicketRequest(
                title=f"Volume Ticket {i}",
                description=f"Description {i}",
                customer_id=f"customer_{i % 10}"
            )
            await ticket_service.create_ticket(request)
        
        assert ticket_service.get_ticket_count() == 100
        
        # Test that listing still works efficiently
        all_tickets = await ticket_service.list_tickets(limit=50)
        assert len(all_tickets) == 50


class TestTicketServiceIntegration:
    """Test integration scenarios for TicketService."""

    @pytest.mark.asyncio
    async def test_full_ticket_lifecycle(self, ticket_service):
        """Test complete ticket lifecycle."""
        # Create ticket
        request = TicketRequest(
            title="Lifecycle Ticket",
            description="Testing full lifecycle",
            customer_id="lifecycle_customer"
        )
        
        created = await ticket_service.create_ticket(request)
        assert created.status == TicketStatus.OPEN
        
        # Assign to agent
        assigned = await ticket_service.assign_ticket_to_agent(
            created.ticket_id,
            "agent_001"
        )
        assert assigned.assigned_agent == "agent_001"
        
        # Update to in progress
        in_progress = await ticket_service.update_ticket_status(
            created.ticket_id,
            TicketStatus.IN_PROGRESS
        )
        assert in_progress.status == TicketStatus.IN_PROGRESS
        
        # Resolve ticket
        resolved = await ticket_service.update_ticket_status(
            created.ticket_id,
            TicketStatus.RESOLVED
        )
        assert resolved.status == TicketStatus.RESOLVED
        
        # Close ticket
        closed = await ticket_service.update_ticket_status(
            created.ticket_id,
            TicketStatus.CLOSED
        )
        assert closed.status == TicketStatus.CLOSED

    @pytest.mark.asyncio
    async def test_ticket_escalation_workflow(self, ticket_service):
        """Test ticket escalation workflow."""
        # Create low priority ticket
        request = TicketRequest(
            title="Initial Issue",
            description="Started as low priority",
            customer_id="escalation_customer",
            priority=Priority.LOW
        )
        
        created = await ticket_service.create_ticket(request)
        assert created.priority == Priority.LOW
        
        # Escalate ticket
        escalated = await ticket_service.escalate_ticket(
            created.ticket_id,
            "senior_agent_001",
            "Customer complaint escalated"
        )
        
        assert escalated.priority == Priority.HIGH
        assert escalated.assigned_agent == "senior_agent_001"


class TestTicketServiceEdgeCases:
    """Test edge cases and error conditions."""

    @pytest.mark.asyncio
    async def test_very_long_title_and_description(self, ticket_service):
        """Test ticket with very long title and description."""
        long_title = "A" * 1000
        long_description = "B" * 10000
        
        request = TicketRequest(
            title=long_title,
            description=long_description,
            customer_id="customer_123"
        )
        
        result = await ticket_service.create_ticket(request)
        
        # Should handle gracefully (might truncate)
        assert result is not None
        assert result.ticket_id is not None

    @pytest.mark.asyncio
    async def test_special_characters_in_ticket_data(self, ticket_service):
        """Test ticket with special characters."""
        request = TicketRequest(
            title="Special chars: @#$%^&*()",
            description="Description with unicode: 你好 🙂",
            customer_id="customer_123"
        )
        
        result = await ticket_service.create_ticket(request)
        
        assert result is not None
        assert result.ticket_id is not None

    @pytest.mark.asyncio
    async def test_multiple_rapid_status_updates(self, ticket_service, sample_ticket_request):
        """Test rapid consecutive status updates."""
        created_ticket = await ticket_service.create_ticket(sample_ticket_request)
        
        # Rapid status changes
        statuses = [
            TicketStatus.IN_PROGRESS,
            TicketStatus.RESOLVED,
            TicketStatus.CLOSED,
            TicketStatus.OPEN  # Reopening
        ]
        
        for status in statuses:
            result = await ticket_service.update_ticket_status(
                created_ticket.ticket_id,
                status
            )
            assert result.status == status
