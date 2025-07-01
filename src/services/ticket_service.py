"""
Ticket service for handling support ticket business logic.
"""
import uuid
from datetime import datetime
from typing import List, Optional

from ..api.schemas import (
    TicketRequest, TicketResponse, TicketStatus, Priority, QueryType
)


class TicketService:
    """Service class for handling ticket-related business logic."""
    
    def __init__(self, db: dict):
        """Initializes the service with a database connection/session."""
        self.tickets_db = db
    
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
        
        # Create ticket data
        ticket_data = {
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
        self.tickets_db[ticket_id] = ticket_data
        
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
