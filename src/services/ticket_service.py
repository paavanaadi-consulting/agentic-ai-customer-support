"""
Ticket service for handling support ticket business logic.
"""
import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any

from ..api.schemas import (
    TicketRequest, TicketResponse, TicketStatus, Priority, QueryType
)
from ..mcp.optimized_postgres_mcp_client import OptimizedPostgreSQLMCPClient, MCPClientError


class TicketService:
    """Service class for handling ticket-related business logic."""
    
    def __init__(self, 
                 mcp_client: Optional[OptimizedPostgreSQLMCPClient] = None,
                 tickets_db: Optional[Dict[str, Any]] = None):
        """Initializes the service with MCP client or in-memory storage."""
        self.mcp_client = mcp_client
        self.tickets_db = tickets_db or {}
    
    async def create_ticket(self, request: TicketRequest) -> TicketResponse:
        """
        Create a new support ticket.
        
        Args:
            request: TicketRequest containing ticket details
            
        Returns:
            TicketResponse with created ticket information
        """
        ticket_id = str(uuid.uuid4())
        now = datetime.utcnow()
        
        # Create ticket data for database
        ticket_data = {
            "ticket_id": ticket_id,
            "customer_id": request.customer_id,
            "subject": request.title,  # Map title to subject (database field)
            "description": request.description,
            "priority": request.priority.value.lower(),
            "status": TicketStatus.OPEN.value.lower(),
            "created_at": now,
        }
        
        # Store ticket using available client
        if self.mcp_client:
            try:
                created_ticket = await self.mcp_client.create_ticket(ticket_data)
                if created_ticket:
                    # Convert to response format
                    response_data = {
                        "ticket_id": created_ticket["ticket_id"],
                        "title": created_ticket["subject"],
                        "description": created_ticket["description"],
                        "customer_id": created_ticket["customer_id"],
                        "category": request.category,
                        "priority": Priority(created_ticket["priority"].upper()),
                        "status": TicketStatus(created_ticket["status"].upper()),
                        "created_at": created_ticket["created_at"],
                        "updated_at": created_ticket.get("updated_at", created_ticket["created_at"]),
                        "tags": request.tags,
                        "assigned_agent": self._auto_assign_agent(request.category, request.priority)
                    }
                    return TicketResponse(**response_data)
                else:
                    raise Exception("Failed to create ticket in database")
            except MCPClientError as e:
                raise Exception(f"Database error: {e}")
        
        # Fallback to in-memory storage
        ticket_data_memory = {
            "ticket_id": ticket_id,
            "title": request.title,
            "description": request.description,
            "customer_id": request.customer_id,
            "category": request.category,
            "priority": request.priority,
            "status": TicketStatus.OPEN,
            "created_at": now,
            "updated_at": now,
            "tags": request.tags,
            "assigned_agent": self._auto_assign_agent(request.category, request.priority)
        }
        
        # Store ticket
        self.tickets_db[ticket_id] = ticket_data_memory
        
        return TicketResponse(
            ticket_id=ticket_id,
            title=request.title,
            status=TicketStatus.OPEN,
            customer_id=request.customer_id,
            created_at=now,
            updated_at=now,
            priority=request.priority,
            category=request.category
        )
    
    async def get_ticket_by_id(self, ticket_id: str) -> Optional[TicketResponse]:
        """
        Retrieve a ticket by its ID.
        
        Args:
            ticket_id: The unique ticket identifier
            
        Returns:
            TicketResponse if found, None otherwise
        """
        # Use MCP client if available
        if self.mcp_client:
            try:
                ticket = await self.mcp_client.get_ticket_by_id(ticket_id)
                if ticket:
                    # Convert database fields to API schema
                    response_data = {
                        "ticket_id": ticket["ticket_id"],
                        "title": ticket["subject"],
                        "description": ticket["description"],
                        "customer_id": ticket["customer_id"],
                        "category": "general",  # Default category
                        "priority": Priority(ticket["priority"].upper()),
                        "status": TicketStatus(ticket["status"].upper()),
                        "created_at": ticket["created_at"],
                        "updated_at": ticket.get("updated_at", ticket["created_at"]),
                        "tags": [],  # Default empty tags
                        "assigned_agent": ticket.get("agent_name")
                    }
                    return TicketResponse(**response_data)
                else:
                    return None
            except MCPClientError as e:
                # Log error and fall back to in-memory if available
                print(f"MCP error in get_ticket_by_id: {e}")
                pass
        
        # Fallback to in-memory storage
        if ticket_id not in self.tickets_db:
            return None
        
        ticket = self.tickets_db[ticket_id]
        return TicketResponse(**ticket)
    
    async def update_ticket_status(
        self, 
        ticket_id: str, 
        status: TicketStatus
    ) -> Optional[TicketResponse]:
        """
        Update the status of a specific ticket.
        
        Args:
            ticket_id: The unique ticket identifier
            status: New ticket status
            
        Returns:
            Updated TicketResponse if found, None otherwise
        """
        # Use MCP client if available
        if self.mcp_client:
            try:
                updates = {
                    "status": status.value.lower(),
                    "updated_at": datetime.utcnow()
                }
                
                # Handle status-specific logic
                if status == TicketStatus.RESOLVED:
                    updates["resolved_at"] = datetime.utcnow()
                
                updated_ticket = await self.mcp_client.update_ticket(ticket_id, updates)
                if updated_ticket:
                    # Handle status-specific logic
                    if status == TicketStatus.IN_PROGRESS:
                        self._handle_ticket_in_progress(ticket_id)
                    elif status == TicketStatus.RESOLVED:
                        self._handle_ticket_resolved(ticket_id)
                    elif status == TicketStatus.CLOSED:
                        self._handle_ticket_closed(ticket_id)
                    
                    # Convert database fields to API schema
                    response_data = {
                        "ticket_id": updated_ticket["ticket_id"],
                        "title": updated_ticket["subject"],
                        "description": updated_ticket["description"],
                        "customer_id": updated_ticket["customer_id"],
                        "category": "general",  # Default category
                        "priority": Priority(updated_ticket["priority"].upper()),
                        "status": TicketStatus(updated_ticket["status"].upper()),
                        "created_at": updated_ticket["created_at"],
                        "updated_at": updated_ticket.get("updated_at", updated_ticket["created_at"]),
                        "tags": [],  # Default empty tags
                        "assigned_agent": updated_ticket.get("agent_name")
                    }
                    return TicketResponse(**response_data)
                else:
                    return None
            except MCPClientError as e:
                # Log error and fall back to in-memory if available
                print(f"MCP error in update_ticket_status: {e}")
                pass
        
        # Fallback to in-memory storage
        if ticket_id not in self.tickets_db:
            return None
        
        # Update ticket status and timestamp
        self.tickets_db[ticket_id]["status"] = status
        self.tickets_db[ticket_id]["updated_at"] = datetime.utcnow()
        
        # Handle status-specific logic
        if status == TicketStatus.IN_PROGRESS:
            self._handle_ticket_in_progress(ticket_id)
        elif status == TicketStatus.RESOLVED:
            self._handle_ticket_resolved(ticket_id)
        elif status == TicketStatus.CLOSED:
            self._handle_ticket_closed(ticket_id)
        
        ticket = self.tickets_db[ticket_id]
        return TicketResponse(**ticket)
    
    async def list_tickets(
        self,
        customer_id: Optional[str] = None,
        status: Optional[TicketStatus] = None,
        priority: Optional[Priority] = None,
        limit: int = 10
    ) -> List[TicketResponse]:
        """
        List tickets with optional filtering.
        
        Args:
            customer_id: Filter by customer ID
            status: Filter by ticket status
            priority: Filter by priority
            limit: Maximum number of results to return
            
        Returns:
            List of TicketResponse objects
        """
        # Use MCP client if available
        if self.mcp_client:
            try:
                # Get tickets from MCP server
                tickets = await self.mcp_client.get_tickets(
                    limit=limit,
                    status=status.value.lower() if status else None
                )
                
                # Convert to response format and apply filters
                result = []
                for ticket in tickets:
                    # Apply client-side filters that aren't supported by MCP server
                    if customer_id and ticket.get("customer_id") != customer_id:
                        continue
                    if priority and ticket.get("priority", "").upper() != priority.value:
                        continue
                    
                    response_data = {
                        "ticket_id": ticket["ticket_id"],
                        "title": ticket["subject"],
                        "description": ticket.get("description", ""),
                        "customer_id": ticket["customer_id"],
                        "category": "general",  # Default category
                        "priority": Priority(ticket["priority"].upper()),
                        "status": TicketStatus(ticket["status"].upper()),
                        "created_at": ticket["created_at"],
                        "updated_at": ticket.get("updated_at", ticket["created_at"]),
                        "tags": [],  # Default empty tags
                        "assigned_agent": ticket.get("agent_name")
                    }
                    result.append(TicketResponse(**response_data))
                    
                    if len(result) >= limit:
                        break
                
                return result
            except MCPClientError as e:
                # Log error and fall back to in-memory if available
                print(f"MCP error in list_tickets: {e}")
                pass
        
        # Fallback to in-memory storage
        filtered_tickets = list(self.tickets_db.values())
        
        # Apply filters
        if customer_id:
            filtered_tickets = [
                t for t in filtered_tickets 
                if t["customer_id"] == customer_id
            ]
        
        if status:
            filtered_tickets = [
                t for t in filtered_tickets 
                if t["status"] == status
            ]
            
        if priority:
            filtered_tickets = [
                t for t in filtered_tickets 
                if t["priority"] == priority
            ]
        
        # Sort by priority and creation date
        filtered_tickets.sort(
            key=lambda x: (
                self._priority_weight(x["priority"]),
                x["created_at"]
            ),
            reverse=True
        )
        
        # Apply limit
        filtered_tickets = filtered_tickets[:limit]
        
        return [TicketResponse(**ticket) for ticket in filtered_tickets]
    
    async def assign_ticket(
        self, 
        ticket_id: str, 
        agent_id: str
    ) -> Optional[TicketResponse]:
        """
        Assign a ticket to an agent.
        
        Args:
            ticket_id: The unique ticket identifier
            agent_id: The agent to assign the ticket to
            
        Returns:
            Updated TicketResponse if found, None otherwise
        """
        if ticket_id not in self.tickets_db:
            return None
        
        self.tickets_db[ticket_id]["assigned_agent"] = agent_id
        self.tickets_db[ticket_id]["updated_at"] = datetime.utcnow()
        
        # Auto-update status if currently open
        if self.tickets_db[ticket_id]["status"] == TicketStatus.OPEN:
            self.tickets_db[ticket_id]["status"] = TicketStatus.IN_PROGRESS
        
        ticket = self.tickets_db[ticket_id]
        return TicketResponse(**ticket)
    
    def _auto_assign_agent(self, category: QueryType, priority: Priority) -> Optional[str]:
        """
        Automatically assign an agent based on category and priority.
        
        Args:
            category: Ticket category
            priority: Ticket priority
            
        Returns:
            Agent ID if auto-assignment is possible, None otherwise
        """
        # Agent assignment logic based on category
        agent_mapping = {
            QueryType.TECHNICAL: "tech_agent_001",
            QueryType.BILLING: "billing_agent_001", 
            QueryType.ACCOUNT: "account_agent_001",
            QueryType.COMPLAINT: "escalation_agent_001",
            QueryType.GENERAL: "general_agent_001"
        }
        
        base_agent = agent_mapping.get(category)
        
        # For critical priority, assign to senior agents
        if priority == Priority.CRITICAL:
            senior_agents = {
                QueryType.TECHNICAL: "senior_tech_agent_001",
                QueryType.BILLING: "senior_billing_agent_001",
                QueryType.COMPLAINT: "senior_escalation_agent_001"
            }
            return senior_agents.get(category, base_agent)
        
        return base_agent
    
    def _priority_weight(self, priority: Priority) -> int:
        """Get numeric weight for priority sorting."""
        weights = {
            Priority.CRITICAL: 4,
            Priority.HIGH: 3,
            Priority.MEDIUM: 2,
            Priority.LOW: 1
        }
        return weights.get(priority, 0)
    
    def _handle_ticket_in_progress(self, ticket_id: str):
        """Handle business logic for tickets moving to in_progress status."""
        # Could send notifications, update metrics, etc.
        pass
    
    def _handle_ticket_resolved(self, ticket_id: str):
        """Handle business logic for tickets moving to resolved status."""
        # Could trigger customer satisfaction survey, update metrics, etc.
        pass
    
    def _handle_ticket_closed(self, ticket_id: str):
        """Handle business logic for tickets moving to closed status."""
        # Could archive ticket, update metrics, send final notifications, etc.
        pass
    
    def get_ticket_count(self) -> int:
        """Get total number of tickets."""
        return len(self.tickets_db)
    
    def get_tickets_by_status(self) -> dict:
        """Get ticket count by status."""
        tickets_by_status = {}
        for ticket in self.tickets_db.values():
            status = ticket["status"].value
            tickets_by_status[status] = tickets_by_status.get(status, 0) + 1
        return tickets_by_status
    
    def get_tickets_by_priority(self) -> dict:
        """Get ticket count by priority."""
        tickets_by_priority = {}
        for ticket in self.tickets_db.values():
            priority = ticket["priority"].value
            tickets_by_priority[priority] = tickets_by_priority.get(priority, 0) + 1
        return tickets_by_priority
