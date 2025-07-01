"""
Refactored API V1 routes using service layer.
All business logic has been extracted to service classes.
Route handlers only manage HTTP concerns.
"""
import time
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query, Path, Depends

from .schemas import (
    QueryRequest, QueryResponse, TicketRequest, TicketResponse,
    CustomerRequest, CustomerResponse, FeedbackRequest, FeedbackResponse,
    AnalyticsResponse, TicketStatus, Priority, QueryType
)
from .dependencies import (
    get_query_service_dep, get_ticket_service_dep, get_customer_service_dep,
    get_feedback_service_dep, get_analytics_service_dep
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
    query_service: QueryService = Depends(get_query_service_dep),
    customer_service: CustomerService = Depends(get_customer_service_dep)
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
    query_service: QueryService = Depends(get_query_service_dep)
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
    query_service: QueryService = Depends(get_query_service_dep)
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
    ticket_service: TicketService = Depends(get_ticket_service_dep),
    customer_service: CustomerService = Depends(get_customer_service_dep)
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
    ticket_service: TicketService = Depends(get_ticket_service_dep)
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
    ticket_service: TicketService = Depends(get_ticket_service_dep)
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
    ticket_service: TicketService = Depends(get_ticket_service_dep)
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
    customer_service: CustomerService = Depends(get_customer_service_dep)
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
    customer_service: CustomerService = Depends(get_customer_service_dep)
):
    """Get a specific customer by their ID."""
    result = await customer_service.get_customer_by_id(customer_id)
    
    if result is None:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    return result


@router.get("/customers", response_model=List[CustomerResponse], summary="List customers")
async def list_customers(
    limit: int = Query(10, ge=1, le=100, description="Number of results to return"),
    customer_service: CustomerService = Depends(get_customer_service_dep)
):
    """List all customers."""
    return await customer_service.list_customers(limit=limit)


# Feedback endpoints
@router.post("/feedback", response_model=FeedbackResponse, summary="Submit feedback")
async def submit_feedback(
    request: FeedbackRequest,
    feedback_service: FeedbackService = Depends(get_feedback_service_dep),
    customer_service: CustomerService = Depends(get_customer_service_dep)
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
    feedback_service: FeedbackService = Depends(get_feedback_service_dep)
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
    analytics_service: AnalyticsService = Depends(get_analytics_service_dep)
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
    analytics_service: AnalyticsService = Depends(get_analytics_service_dep)
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
    analytics_service: AnalyticsService = Depends(get_analytics_service_dep)
):
    """Get customer-focused analytics and insights."""
    try:
        return await analytics_service.get_customer_insights()
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Customer insights retrieval failed: {str(e)}"
        )


# Health and status endpoints
@router.get("/status", response_model=dict, summary="Get API status")
async def get_api_status(
    analytics_service: AnalyticsService = Depends(get_analytics_service_dep)
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
                "feedback": basic_analytics.total_queries  # Will be updated with proper count
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

# Query endpoints
@router.post("/queries", response_model=QueryResponse, summary="Process customer query")
async def process_query(request: QueryRequest):
    """
    Process a customer query using AI agents.
    
    This endpoint processes customer queries and returns intelligent responses
    using the agentic AI system.
    """
    try:
        query_id = str(uuid.uuid4())
        processing_start = time.time()
        
        # Simulate query processing with different agents
        agent_mapping = {
            QueryType.TECHNICAL: "technical_agent",
            QueryType.BILLING: "billing_agent", 
            QueryType.ACCOUNT: "account_agent",
            QueryType.COMPLAINT: "response_agent",
            QueryType.GENERAL: "general_agent"
        }
        
        agent_used = agent_mapping.get(request.query_type, "general_agent")
        
        # Simulate processing time
        processing_time = time.time() - processing_start
        
        # Mock response generation
        response_mapping = {
            QueryType.TECHNICAL: f"Technical support response for: {request.query[:50]}...",
            QueryType.BILLING: f"Billing inquiry handled: {request.query[:50]}...",
            QueryType.ACCOUNT: f"Account information: {request.query[:50]}...",
            QueryType.COMPLAINT: f"We apologize for the inconvenience regarding: {request.query[:50]}...",
            QueryType.GENERAL: f"Thank you for your inquiry: {request.query[:50]}..."
        }
        
        result = response_mapping.get(request.query_type, f"Response to: {request.query}")
        
        # Store query
        query_data = {
            "query_id": query_id,
            "customer_id": request.customer_id,
            "query": request.query,
            "query_type": request.query_type,
            "priority": request.priority,
            "result": result,
            "agent_used": agent_used,
            "processing_time": processing_time,
            "timestamp": datetime.utcnow(),
            "context": request.context
        }
        queries_db[query_id] = query_data
        
        return QueryResponse(
            query_id=query_id,
            result=result,
            confidence=0.85,  # Mock confidence score
            success=True,
            agent_used=agent_used,
            processing_time=processing_time,
            suggestions=[
                "Check our FAQ section",
                "Consider scheduling a call",
                "Review our documentation"
            ]
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query processing failed: {str(e)}")

@router.get("/queries/{query_id}", response_model=QueryResponse, summary="Get query by ID")
async def get_query(query_id: str = Path(..., description="Query ID")):
    """Get a specific query by its ID."""
    if query_id not in queries_db:
        raise HTTPException(status_code=404, detail="Query not found")
    
    query = queries_db[query_id]
    return QueryResponse(
        query_id=query["query_id"],
        result=query["result"],
        confidence=0.85,
        success=True,
        agent_used=query["agent_used"],
        processing_time=query["processing_time"],
        suggestions=[],
        timestamp=query["timestamp"]
    )

@router.get("/queries", response_model=List[QueryResponse], summary="List queries")
async def list_queries(
    customer_id: Optional[str] = Query(None, description="Filter by customer ID"),
    query_type: Optional[QueryType] = Query(None, description="Filter by query type"),
    limit: int = Query(10, ge=1, le=100, description="Number of results to return")
):
    """List queries with optional filtering."""
    filtered_queries = list(queries_db.values())
    
    if customer_id:
        filtered_queries = [q for q in filtered_queries if q["customer_id"] == customer_id]
    
    if query_type:
        filtered_queries = [q for q in filtered_queries if q["query_type"] == query_type]
    
    # Apply limit
    filtered_queries = filtered_queries[:limit]
    
    return [
        QueryResponse(
            query_id=q["query_id"],
            result=q["result"],
            confidence=0.85,
            success=True,
            agent_used=q["agent_used"],
            processing_time=q["processing_time"],
            suggestions=[],
            timestamp=q["timestamp"]
        )
        for q in filtered_queries
    ]

# Ticket endpoints
@router.post("/tickets", response_model=TicketResponse, summary="Create support ticket")
async def create_ticket(
    request: TicketRequest,
    ticket_service: TicketService = Depends(get_ticket_service)
):
    """Create a new support ticket."""
    return await ticket_service.create_ticket(request)

@router.get("/tickets/{ticket_id}", response_model=TicketResponse, summary="Get ticket by ID")
async def get_ticket(
    ticket_id: str = Path(..., description="Ticket ID"),
    ticket_service: TicketService = Depends(get_ticket_service)
):
    """Get a specific ticket by its ID."""
    ticket = await ticket_service.get_ticket_by_id(ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return ticket

@router.put("/tickets/{ticket_id}/status", response_model=TicketResponse, summary="Update ticket status")
async def update_ticket_status(
    ticket_id: str = Path(..., description="Ticket ID"),
    status: TicketStatus = Query(..., description="New ticket status"),
    ticket_service: TicketService = Depends(get_ticket_service)
):
    """Update the status of a specific ticket."""
    updated_ticket = await ticket_service.update_ticket_status(ticket_id, status)
    if not updated_ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return updated_ticket

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
async def create_customer(request: CustomerRequest):
    """Create a new customer profile."""
    customer_id = str(uuid.uuid4())
    now = datetime.utcnow()
    
    customer_data = {
        "customer_id": customer_id,
        "name": request.name,
        "email": request.email,
        "phone": request.phone,
        "company": request.company,
        "created_at": now,
        "metadata": request.metadata,
        "ticket_count": 0,
        "last_interaction": None
    }
    
    customers_db[customer_id] = customer_data
    
    return CustomerResponse(**customer_data)

@router.get("/customers/{customer_id}", response_model=CustomerResponse, summary="Get customer by ID")
async def get_customer(customer_id: str = Path(..., description="Customer ID")):
    """Get a specific customer by their ID."""
    if customer_id not in customers_db:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    customer = customers_db[customer_id]
    return CustomerResponse(**customer)

@router.get("/customers", response_model=List[CustomerResponse], summary="List customers")
async def list_customers(
    limit: int = Query(10, ge=1, le=100, description="Number of results to return")
):
    """List all customers."""
    customers = list(customers_db.values())[:limit]
    return [CustomerResponse(**customer) for customer in customers]

# Feedback endpoints
@router.post("/feedback", response_model=FeedbackResponse, summary="Submit feedback")
async def submit_feedback(request: FeedbackRequest):
    """Submit customer feedback."""
    feedback_id = str(uuid.uuid4())
    now = datetime.utcnow()
    
    feedback_data = {
        "feedback_id": feedback_id,
        "customer_id": request.customer_id,
        "rating": request.rating,
        "comment": request.comment,
        "query_id": request.query_id,
        "ticket_id": request.ticket_id,
        "created_at": now
    }
    
    feedback_db[feedback_id] = feedback_data
    
    return FeedbackResponse(**feedback_data)

@router.get("/feedback", response_model=List[FeedbackResponse], summary="List feedback")
async def list_feedback(
    customer_id: Optional[str] = Query(None, description="Filter by customer ID"),
    rating: Optional[int] = Query(None, ge=1, le=5, description="Filter by rating"),
    limit: int = Query(10, ge=1, le=100, description="Number of results to return")
):
    """List feedback with optional filtering."""
    filtered_feedback = list(feedback_db.values())
    
    if customer_id:
        filtered_feedback = [f for f in filtered_feedback if f["customer_id"] == customer_id]
    
    if rating:
        filtered_feedback = [f for f in filtered_feedback if f["rating"] == rating]
    
    # Apply limit
    filtered_feedback = filtered_feedback[:limit]
    
    return [FeedbackResponse(**feedback) for feedback in filtered_feedback]

# Analytics endpoints
@router.get("/analytics", response_model=AnalyticsResponse, summary="Get analytics data")
async def get_analytics():
    """Get system analytics and metrics."""
    
    # Calculate metrics from in-memory data
    total_queries = len(queries_db)
    total_tickets = len(tickets_db)
    total_customers = len(customers_db)
    
    # Calculate average response time
    if queries_db:
        avg_response_time = sum(q["processing_time"] for q in queries_db.values()) / len(queries_db)
    else:
        avg_response_time = 0.0
    
    # Calculate average rating
    if feedback_db:
        avg_rating = sum(f["rating"] for f in feedback_db.values()) / len(feedback_db)
    else:
        avg_rating = 0.0
    
    # Tickets by status
    tickets_by_status = {}
    for ticket in tickets_db.values():
        status = ticket["status"].value
        tickets_by_status[status] = tickets_by_status.get(status, 0) + 1
    
    # Queries by type
    queries_by_type = {}
    for query in queries_db.values():
        query_type = query["query_type"].value
        queries_by_type[query_type] = queries_by_type.get(query_type, 0) + 1
    
    return AnalyticsResponse(
        total_queries=total_queries,
        total_tickets=total_tickets,
        total_customers=total_customers,
        avg_response_time=avg_response_time,
        avg_rating=avg_rating,
        tickets_by_status=tickets_by_status,
        queries_by_type=queries_by_type
    )

# Health and status endpoints
@router.get("/status", response_model=dict, summary="Get API status")
async def get_api_status():
    """Get detailed API status information."""
    return {
        "status": "operational",
        "version": "1.0.0",
        "uptime": time.time(),
        "endpoints": {
            "queries": len(queries_db),
            "tickets": len(tickets_db),
            "customers": len(customers_db),
            "feedback": len(feedback_db)
        },
        "timestamp": datetime.utcnow()
    }
