"""
MCP Client Interface
Defines a common interface for all MCP clients to ensure consistency
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional


class MCPClientInterface(ABC):
    """Abstract base class for MCP clients."""
    
    @abstractmethod
    async def connect(self) -> bool:
        """Connect to the MCP server."""
        pass
    
    @abstractmethod
    async def disconnect(self):
        """Disconnect from the MCP server."""
        pass
    
    # Customer operations
    @abstractmethod
    async def get_customers(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get customers from the database."""
        pass
    
    @abstractmethod
    async def get_customer_by_id(self, customer_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific customer by ID."""
        pass
    
    @abstractmethod
    async def create_customer(self, customer_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new customer."""
        pass
    
    @abstractmethod
    async def update_customer(self, customer_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update customer information."""
        pass
    
    # Ticket operations
    @abstractmethod
    async def get_tickets(self, limit: int = 100, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get tickets from the database."""
        pass
    
    @abstractmethod
    async def get_ticket_by_id(self, ticket_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific ticket by ID."""
        pass
    
    @abstractmethod
    async def create_ticket(self, ticket_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new ticket."""
        pass
    
    @abstractmethod
    async def update_ticket(self, ticket_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update ticket information."""
        pass
    
    # Knowledge base operations
    @abstractmethod
    async def search_knowledge_base(self, search_term: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search the knowledge base."""
        pass
    
    # Analytics operations
    @abstractmethod
    async def get_analytics(self, days: int = 30) -> Dict[str, Any]:
        """Get analytics data."""
        pass
