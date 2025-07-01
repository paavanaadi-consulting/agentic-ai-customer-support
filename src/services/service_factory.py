"""
Service factory for dependency injection and service management.
"""
from functools import lru_cache
from typing import Optional, Union

from .query_service import QueryService
from .ticket_service import TicketService
from .customer_service import CustomerService
from .feedback_service import FeedbackService
from .analytics_service import AnalyticsService
from ..mcp.optimized_postgres_mcp_client import OptimizedPostgreSQLMCPClient, get_optimized_mcp_client


class ServiceFactory:
    """Factory class for creating and managing service instances."""
    
    def __init__(self, 
                 mcp_client: Optional[OptimizedPostgreSQLMCPClient] = None):
        self._query_service = None
        self._ticket_service = None
        self._customer_service = None
        self._feedback_service = None
        self._analytics_service = None
        self._mcp_client = mcp_client
        
        # In-memory database fallback (if MCP client not provided)
        self._tickets_db = {}
    
    @property
    def query_service(self) -> QueryService:
        """Get or create QueryService instance."""
        if self._query_service is None:
            self._query_service = QueryService()
        return self._query_service
    
    @property
    def customer_service(self) -> CustomerService:
        """Get or create CustomerService instance."""
        if self._customer_service is None:
            if self._mcp_client:
                self._customer_service = CustomerService(mcp_client=self._mcp_client)
            else:
                # Fallback to in-memory storage
                self._customer_service = CustomerService()
        return self._customer_service
    
    @property
    def ticket_service(self) -> TicketService:
        """Get or create TicketService instance."""
        if self._ticket_service is None:
            if self._mcp_client:
                self._ticket_service = TicketService(mcp_client=self._mcp_client)
            else:
                # Fallback to in-memory storage
                self._ticket_service = TicketService(tickets_db=self._tickets_db)
        return self._ticket_service
    
    @property
    def feedback_service(self) -> FeedbackService:
        """Get or create FeedbackService instance."""
        if self._feedback_service is None:
            self._feedback_service = FeedbackService()
        return self._feedback_service
    
    @property
    def analytics_service(self) -> AnalyticsService:
        """Get or create AnalyticsService instance."""
        if self._analytics_service is None:
            if self._mcp_client:
                self._analytics_service = AnalyticsService(
                    query_service=self.query_service,
                    mcp_client=self._mcp_client
                )
            else:
                self._analytics_service = AnalyticsService(
                    query_service=self.query_service,
                    ticket_service=self.ticket_service,
                    customer_service=self.customer_service,
                    feedback_service=self.feedback_service
                )
        return self._analytics_service


# Global service factory instance
_service_factory: Optional[ServiceFactory] = None

def initialize_service_factory(
    mcp_client: Optional[OptimizedPostgreSQLMCPClient] = None
) -> ServiceFactory:
    """Initialize the global service factory with MCP client."""
    global _service_factory
    _service_factory = ServiceFactory(mcp_client=mcp_client)
    return _service_factory

async def initialize_service_factory_with_optimized_mcp_default() -> ServiceFactory:
    """Initialize the global service factory with default optimized MCP client."""
    optimized_client = await get_optimized_mcp_client()
    return initialize_service_factory(mcp_client=optimized_client)

async def initialize_service_factory_with_optimized_mcp(
    connection_string: Optional[str] = None,
    mcp_server_url: str = "http://localhost:8001",
    use_direct_connection: bool = True
) -> ServiceFactory:
    """Initialize the global service factory with optimized MCP client."""
    optimized_client = await get_optimized_mcp_client(
        connection_string=connection_string,
        mcp_server_url=mcp_server_url,
        use_direct_connection=use_direct_connection
    )
    return initialize_service_factory(mcp_client=optimized_client)

@lru_cache()
def get_service_factory() -> ServiceFactory:
    """Get singleton ServiceFactory instance."""
    global _service_factory
    if _service_factory is None:
        # Initialize without database client (fallback to in-memory)
        _service_factory = ServiceFactory()
    return _service_factory


# Convenience functions for getting individual services
def get_query_service() -> QueryService:
    """Get QueryService instance."""
    return get_service_factory().query_service


def get_ticket_service() -> TicketService:
    """Get TicketService instance."""
    return get_service_factory().ticket_service


def get_customer_service() -> CustomerService:
    """Get CustomerService instance."""
    return get_service_factory().customer_service


def get_feedback_service() -> FeedbackService:
    """Get FeedbackService instance."""
    return get_service_factory().feedback_service


def get_analytics_service() -> AnalyticsService:
    """Get AnalyticsService instance."""
    return get_service_factory().analytics_service
