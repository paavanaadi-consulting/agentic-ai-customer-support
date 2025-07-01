"""
FastAPI dependency providers for services and repositories.

This module centralizes the instantiation of services, making it easy
to manage dependencies and switch implementations (e.g., from in-memory
to a real database).
"""

from fastapi import HTTPException

from ..services.service_factory import (
    get_query_service, get_ticket_service, get_customer_service,
    get_feedback_service, get_analytics_service, get_kafka_client
)
from ..services.query_service import QueryService
from ..services.ticket_service import TicketService
from ..services.customer_service import CustomerService
from ..services.feedback_service import FeedbackService
from ..services.analytics_service import AnalyticsService
from ..mcp.kafka_mcp_client import OptimizedKafkaMCPClient


# Export list for better IDE support
__all__ = [
    "get_query_service_dep",
    "get_ticket_service_dep", 
    "get_customer_service_dep",
    "get_feedback_service_dep",
    "get_analytics_service_dep",
    "get_kafka_client_dep"
]


# Dependency providers - using service factory for singleton behavior
def get_query_service_dep() -> QueryService:
    """Dependency provider for the QueryService."""
    return get_query_service()


def get_ticket_service_dep() -> TicketService:
    """Dependency provider for the TicketService."""
    return get_ticket_service()


def get_customer_service_dep() -> CustomerService:
    """Dependency provider for the CustomerService."""
    return get_customer_service()


def get_feedback_service_dep() -> FeedbackService:
    """Dependency provider for the FeedbackService."""
    return get_feedback_service()


def get_analytics_service_dep() -> AnalyticsService:
    """Dependency provider for the AnalyticsService."""
    return get_analytics_service()


def get_kafka_client_dep() -> OptimizedKafkaMCPClient:
    """Dependency provider for the Kafka MCP Client."""
    kafka_client = get_kafka_client()
    if kafka_client is None:
        raise HTTPException(status_code=503, detail="Kafka MCP client not available")
    return kafka_client