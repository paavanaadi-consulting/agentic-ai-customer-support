"""
Service factory for dependency injection and service management.
"""
from functools import lru_cache

from .query_service import QueryService
from .ticket_service import TicketService
from .customer_service import CustomerService
from .feedback_service import FeedbackService
from .analytics_service import AnalyticsService


class ServiceFactory:
    """Factory class for creating and managing service instances."""
    
    def __init__(self):
        self._query_service = None
        self._ticket_service = None
        self._customer_service = None
        self._feedback_service = None
        self._analytics_service = None
        
        # In-memory database for ticket service (only one that needs external db)
        self._tickets_db = {}
    
    @property
    def query_service(self) -> QueryService:
        """Get or create QueryService instance."""
        if self._query_service is None:
            self._query_service = QueryService()
        return self._query_service
    
    @property
    def ticket_service(self) -> TicketService:
        """Get or create TicketService instance."""
        if self._ticket_service is None:
            self._ticket_service = TicketService(self._tickets_db)
        return self._ticket_service
    
    @property
    def customer_service(self) -> CustomerService:
        """Get or create CustomerService instance."""
        if self._customer_service is None:
            self._customer_service = CustomerService()
        return self._customer_service
    
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
            self._analytics_service = AnalyticsService(
                query_service=self.query_service,
                ticket_service=self.ticket_service,
                customer_service=self.customer_service,
                feedback_service=self.feedback_service
            )
        return self._analytics_service


# Global service factory instance
@lru_cache()
def get_service_factory() -> ServiceFactory:
    """Get singleton ServiceFactory instance."""
    return ServiceFactory()


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
