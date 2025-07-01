"""
Refactored API V1 routes using service layer.
All business logic has been extracted to service classes.
Route handlers only manage HTTP concerns.
"""
import time
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query, Path, Depends
from fastapi.responses import JSONResponse

from .schemas import (
    QueryRequest, QueryResponse, TicketRequest, TicketResponse,
    CustomerRequest, CustomerResponse, FeedbackRequest, FeedbackResponse,
    AnalyticsResponse, ErrorResponse, SuccessResponse,
    TicketStatus, Priority, QueryType
)
from ..services.service_factory import (
    get_query_service, get_ticket_service, get_customer_service,
    get_feedback_service, get_analytics_service
)
from ..services.query_service import QueryService
from ..services.ticket_service import TicketService
from ..services.customer_service import CustomerService
from ..services.feedback_service import FeedbackService
from ..services.analytics_service import AnalyticsService

router = APIRouter()


# Query endpoints
@router.post("/queries", response_model=QueryResponse, summary="Process customer query")
async def process_query(
    request: QueryRequest,
    query_service: QueryService = Depends(get_query_service),
    customer_service: CustomerService = Depends(get_customer_service)
):
    """
    Process a customer query using AI agents.
    
    This endpoint processes customer queries and returns intelligent responses
    using the agentic AI system.
    """
    try:
        # Update customer last interaction
        await customer_service.update_last_interaction(request.customer_id)
        
        # Process the query
        result = await query_service.process_query(request)
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Query processing failed: {str(e)}"
        )


@router.get("/queries/{query_id}", response_model=QueryResponse, summary="Get query by ID")
async def get_query(
    query_id: str = Path(..., description="Query ID"),
    query_service: QueryService = Depends(get_query_service)
):
    """Get a specific query by its ID."""
    result = await query_service.get_query_by_id(query_id)
    
    if result is None:
        raise HTTPException(status_code=404, detail="Query not found")
    
    return result


@router.get("/queries", response_model=List[QueryResponse], summary="List queries")
async def list_queries(
    customer_id: Optional[str] = Query(None, description="Filter by customer ID"),
    query_type: Optional[QueryType] = Query(None, description="Filter by query type"),
    limit: int = Query(10, ge=1, le=100, description="Number of results to return"),
    query_service: QueryService = Depends(get_query_service)
):
    """List queries with optional filtering."""
    return await query_service.list_queries(
        customer_id=customer_id,
        query_type=query_type,
        limit=limit
    )


# Ticket endpoints
@router.post("/tickets", response_model=TicketResponse, summary="Create support ticket")
async def create_ticket(
    request: TicketRequest,
    ticket_service: TicketService = Depends(get_ticket_service),
    customer_service: CustomerService = Depends(get_customer_service)
):
    """Create a new support ticket."""
    try:
        # Update customer metrics
        await customer_service.update_last_interaction(request.customer_id)
        await customer_service.increment_ticket_count(request.customer_id)
        
        # Create the ticket
        result = await ticket_service.create_ticket(request)
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Ticket creation failed: {str(e)}"
        )


@router.get("/tickets/{ticket_id}", response_model=TicketResponse, summary="Get ticket by ID")
async def get_ticket(
    ticket_id: str = Path(..., description="Ticket ID"),
    ticket_service: TicketService = Depends(get_ticket_service)
):
    """Get a specific ticket by its ID."""
    result = await ticket_service.get_ticket_by_id(ticket_id)
    
    if result is None:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    return result


@router.put("/tickets/{ticket_id}/status", response_model=TicketResponse, summary="Update ticket status")
async def update_ticket_status(
    ticket_id: str = Path(..., description="Ticket ID"),
    status: TicketStatus = Query(..., description="New ticket status"),
    ticket_service: TicketService = Depends(get_ticket_service)
):
    """Update the status of a specific ticket."""
    result = await ticket_service.update_ticket_status(ticket_id, status)
    
    if result is None:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    return result


@router.get("/tickets", response_model=List[TicketResponse], summary="List tickets")
async def list_tickets(
    customer_id: Optional[str] = Query(None, description="Filter by customer ID"),
    status: Optional[TicketStatus] = Query(None, description="Filter by status"),
    priority: Optional[Priority] = Query(None, description="Filter by priority"),
    limit: int = Query(10, ge=1, le=100, description="Number of results to return"),
    ticket_service: TicketService = Depends(get_ticket_service)
):
    """List tickets with optional filtering."""
    return await ticket_service.list_tickets(
        customer_id=customer_id,
        status=status,
        priority=priority,
        limit=limit
    )


# Customer endpoints
@router.post("/customers", response_model=CustomerResponse, summary="Create customer")
async def create_customer(
    request: CustomerRequest,
    customer_service: CustomerService = Depends(get_customer_service)
):
    """Create a new customer profile."""
    try:
        result = await customer_service.create_customer(request)
        return result
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Customer creation failed: {str(e)}"
        )


@router.get("/customers/{customer_id}", response_model=CustomerResponse, summary="Get customer by ID")
async def get_customer(
    customer_id: str = Path(..., description="Customer ID"),
    customer_service: CustomerService = Depends(get_customer_service)
):
    """Get a specific customer by their ID."""
    result = await customer_service.get_customer_by_id(customer_id)
    
    if result is None:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    return result


@router.get("/customers", response_model=List[CustomerResponse], summary="List customers")
async def list_customers(
    limit: int = Query(10, ge=1, le=100, description="Number of results to return"),
    customer_service: CustomerService = Depends(get_customer_service)
):
    """List all customers."""
    return await customer_service.list_customers(limit=limit)


# Feedback endpoints
@router.post("/feedback", response_model=FeedbackResponse, summary="Submit feedback")
async def submit_feedback(
    request: FeedbackRequest,
    feedback_service: FeedbackService = Depends(get_feedback_service),
    customer_service: CustomerService = Depends(get_customer_service)
):
    """Submit customer feedback."""
    try:
        # Update customer last interaction
        await customer_service.update_last_interaction(request.customer_id)
        
        # Submit feedback
        result = await feedback_service.submit_feedback(request)
        return result
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Feedback submission failed: {str(e)}"
        )


@router.get("/feedback", response_model=List[FeedbackResponse], summary="List feedback")
async def list_feedback(
    customer_id: Optional[str] = Query(None, description="Filter by customer ID"),
    rating: Optional[int] = Query(None, ge=1, le=5, description="Filter by rating"),
    limit: int = Query(10, ge=1, le=100, description="Number of results to return"),
    feedback_service: FeedbackService = Depends(get_feedback_service)
):
    """List feedback with optional filtering."""
    return await feedback_service.list_feedback(
        customer_id=customer_id,
        rating=rating,
        limit=limit
    )


# Analytics endpoints
@router.get("/analytics", response_model=AnalyticsResponse, summary="Get analytics data")
async def get_analytics(
    analytics_service: AnalyticsService = Depends(get_analytics_service)
):
    """Get system analytics and metrics."""
    try:
        return await analytics_service.get_system_analytics()
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Analytics retrieval failed: {str(e)}"
        )


@router.get("/analytics/performance", response_model=dict, summary="Get performance metrics")
async def get_performance_metrics(
    analytics_service: AnalyticsService = Depends(get_analytics_service)
):
    """Get detailed performance metrics."""
    try:
        return await analytics_service.get_performance_metrics()
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Performance metrics retrieval failed: {str(e)}"
        )


@router.get("/analytics/customers", response_model=dict, summary="Get customer insights")
async def get_customer_insights(
    analytics_service: AnalyticsService = Depends(get_analytics_service)
):
    """Get customer-focused analytics and insights."""
    try:
        return await analytics_service.get_customer_insights()
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Customer insights retrieval failed: {str(e)}"
        )


@router.get("/analytics/agents", response_model=dict, summary="Get agent performance")
async def get_agent_performance(
    analytics_service: AnalyticsService = Depends(get_analytics_service)
):
    """Get agent performance analytics."""
    try:
        return await analytics_service.get_agent_performance()
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Agent performance retrieval failed: {str(e)}"
        )


# Additional customer endpoints
@router.get("/customers/{customer_id}/summary", response_model=dict, summary="Get customer summary")
async def get_customer_summary(
    customer_id: str = Path(..., description="Customer ID"),
    customer_service: CustomerService = Depends(get_customer_service)
):
    """Get comprehensive customer activity summary."""
    result = await customer_service.get_customer_summary(customer_id)
    
    if result is None:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    return result


@router.get("/feedback/analytics", response_model=dict, summary="Get feedback analytics")
async def get_feedback_analytics(
    feedback_service: FeedbackService = Depends(get_feedback_service)
):
    """Get comprehensive feedback analytics."""
    try:
        return await feedback_service.get_feedback_analytics()
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Feedback analytics retrieval failed: {str(e)}"
        )


# Health and status endpoints
@router.get("/status", response_model=dict, summary="Get API status")
async def get_api_status(
    analytics_service: AnalyticsService = Depends(get_analytics_service)
):
    """Get detailed API status information."""
    try:
        # Get basic metrics from analytics service
        basic_analytics = await analytics_service.get_system_analytics()
        
        return {
            "status": "operational",
            "version": "1.0.0",
            "uptime": time.time(),
            "endpoints": {
                "queries": basic_analytics.total_queries,
                "tickets": basic_analytics.total_tickets,
                "customers": basic_analytics.total_customers,
                "feedback": await analytics_service.feedback_service.get_feedback_count()
            },
            "performance": {
                "avg_response_time": basic_analytics.avg_response_time,
                "avg_rating": basic_analytics.avg_rating
            },
            "timestamp": datetime.utcnow()
        }
    except Exception as e:
        # Fallback to basic status if analytics fail
        return {
            "status": "operational",
            "version": "1.0.0",
            "uptime": time.time(),
            "timestamp": datetime.utcnow(),
            "note": "Limited metrics available"
        }
