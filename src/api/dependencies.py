"""
FastAPI dependency providers for services and repositories.

This module centralizes the instantiation of services, making it easy
to manage dependencies and switch implementations (e.g., from in-memory
to a real database).
"""
from functools import lru_cache

from ..services.ticket_service import TicketService

# In-memory storage for demo purposes. In a real app, this would be
# managed by a repository layer that connects to a database.
TICKETS_DB = {}


@lru_cache()
def get_ticket_service() -> TicketService:
    """Dependency provider for the TicketService."""
    # The service now gets its database from the dependency provider.
    return TicketService(db=TICKETS_DB)