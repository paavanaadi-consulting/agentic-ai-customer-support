"""
Pydantic schemas for API requests and responses.
"""
from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum

# Enums
class QueryType(str, Enum):
    GENERAL = "general"
    TECHNICAL = "technical"
    BILLING = "billing"
    ACCOUNT = "account"
    COMPLAINT = "complaint"

class Priority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class TicketStatus(str, Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    PENDING = "pending"
    RESOLVED = "resolved"
    CLOSED = "closed"

# Request Models
class QueryRequest(BaseModel):
    query: str = Field(..., description="Customer query text")
    customer_id: str = Field(..., description="Unique customer identifier")
    query_type: Optional[QueryType] = Field(QueryType.GENERAL, description="Type of query")
    priority: Optional[Priority] = Field(Priority.MEDIUM, description="Query priority")
    context: Dict[str, Any] = Field(default_factory=dict, description="Additional context")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Query metadata")

class TicketRequest(BaseModel):
    title: str = Field(..., description="Ticket title")
    description: str = Field(..., description="Detailed description")
    customer_id: str = Field(..., description="Customer identifier")
    category: QueryType = Field(QueryType.GENERAL, description="Ticket category")
    priority: Priority = Field(Priority.MEDIUM, description="Ticket priority")
    tags: List[str] = Field(default_factory=list, description="Ticket tags")

class CustomerRequest(BaseModel):
    name: str = Field(..., description="Customer name")
    email: str = Field(..., description="Customer email")
    phone: Optional[str] = Field(None, description="Customer phone")
    company: Optional[str] = Field(None, description="Customer company")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Customer metadata")

class FeedbackRequest(BaseModel):
    customer_id: str = Field(..., description="Customer identifier")
    rating: int = Field(..., ge=1, le=5, description="Rating from 1 to 5")
    comment: Optional[str] = Field(None, description="Feedback comment")
    query_id: Optional[str] = Field(None, description="Related query ID")
    ticket_id: Optional[str] = Field(None, description="Related ticket ID")

# Response Models
class QueryResponse(BaseModel):
    query_id: str = Field(..., description="Unique query identifier")
    result: str = Field(..., description="Query result/answer")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score")
    success: bool = Field(..., description="Query success status")
    agent_used: str = Field(..., description="Agent that processed the query")
    processing_time: float = Field(..., description="Processing time in seconds")
    suggestions: List[str] = Field(default_factory=list, description="Related suggestions")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")

class TicketResponse(BaseModel):
    ticket_id: str = Field(..., description="Unique ticket identifier")
    title: str = Field(..., description="Ticket title")
    status: TicketStatus = Field(..., description="Ticket status")
    customer_id: str = Field(..., description="Customer identifier")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    priority: Priority = Field(..., description="Ticket priority")
    category: QueryType = Field(..., description="Ticket category")
    assigned_agent: Optional[str] = Field(None, description="Assigned agent")

class CustomerResponse(BaseModel):
    customer_id: str = Field(..., description="Unique customer identifier")
    name: str = Field(..., description="Customer name")
    email: str = Field(..., description="Customer email")
    phone: Optional[str] = Field(None, description="Customer phone")
    company: Optional[str] = Field(None, description="Customer company")
    created_at: datetime = Field(..., description="Creation timestamp")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Customer metadata")
    ticket_count: int = Field(0, description="Number of tickets")
    last_interaction: Optional[datetime] = Field(None, description="Last interaction timestamp")

class FeedbackResponse(BaseModel):
    feedback_id: str = Field(..., description="Unique feedback identifier")
    customer_id: str = Field(..., description="Customer identifier")
    rating: int = Field(..., description="Rating from 1 to 5")
    comment: Optional[str] = Field(None, description="Feedback comment")
    query_id: Optional[str] = Field(None, description="Related query ID")
    ticket_id: Optional[str] = Field(None, description="Related ticket ID")
    created_at: datetime = Field(..., description="Creation timestamp")

class AnalyticsResponse(BaseModel):
    total_queries: int = Field(..., description="Total number of queries")
    total_tickets: int = Field(..., description="Total number of tickets")
    total_customers: int = Field(..., description="Total number of customers")
    avg_response_time: float = Field(..., description="Average response time")
    avg_rating: float = Field(..., description="Average customer rating")
    tickets_by_status: Dict[str, int] = Field(..., description="Tickets grouped by status")
    queries_by_type: Dict[str, int] = Field(..., description="Queries grouped by type")
    customer_satisfaction_rate: Optional[float] = Field(None, description="Customer satisfaction rate")
    resolution_rate: Optional[float] = Field(None, description="Ticket resolution rate")
    additional_metrics: Optional[Dict[str, Any]] = Field(None, description="Additional system metrics")

# Generic Response Models
class ErrorResponse(BaseModel):
    error: str = Field(..., description="Error message")
    error_code: str = Field(..., description="Error code")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Error timestamp")

class SuccessResponse(BaseModel):
    message: str = Field(..., description="Success message")
    success: bool = Field(True, description="Success status")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")
