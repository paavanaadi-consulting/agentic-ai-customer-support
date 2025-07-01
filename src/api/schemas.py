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

# Kafka/Streaming Models
class KafkaMessageRequest(BaseModel):
    topic: str = Field(..., description="Kafka topic name")
    message: Dict[str, Any] = Field(..., description="Message content")
    key: Optional[str] = Field(None, description="Message key for partitioning")

class KafkaMessageResponse(BaseModel):
    success: bool = Field(..., description="Whether message was published successfully")
    topic: str = Field(..., description="Topic where message was published")
    partition: Optional[int] = Field(None, description="Partition number")
    offset: Optional[int] = Field(None, description="Message offset")
    timestamp: Optional[datetime] = Field(None, description="Message timestamp")

class KafkaTopicRequest(BaseModel):
    topic: str = Field(..., description="Topic name to create")
    num_partitions: int = Field(3, description="Number of partitions")
    replication_factor: int = Field(1, description="Replication factor")

class KafkaTopicResponse(BaseModel):
    success: bool = Field(..., description="Whether topic was created successfully")
    topic: str = Field(..., description="Topic name")
    partitions: int = Field(..., description="Number of partitions")
    replication_factor: int = Field(..., description="Replication factor")

class KafkaConsumeRequest(BaseModel):
    topic: str = Field(..., description="Topic to consume from")
    max_messages: int = Field(10, description="Maximum number of messages to consume")
    timeout_ms: int = Field(5000, description="Consumer timeout in milliseconds")

class KafkaConsumeResponse(BaseModel):
    success: bool = Field(..., description="Whether consumption was successful")
    messages: List[Dict[str, Any]] = Field(..., description="Consumed messages")
    count: int = Field(..., description="Number of messages consumed")

class StreamingQueryRequest(BaseModel):
    query: str = Field(..., description="Customer query text")
    customer_id: str = Field(..., description="Unique customer identifier")
    stream_response: bool = Field(True, description="Whether to stream the response")
    callback_url: Optional[str] = Field(None, description="Callback URL for async responses")

class StreamingQueryResponse(BaseModel):
    query_id: str = Field(..., description="Unique query identifier")
    status: str = Field(..., description="Processing status")
    stream_id: Optional[str] = Field(None, description="Stream identifier for real-time updates")
    estimated_completion: Optional[datetime] = Field(None, description="Estimated completion time")

# Additional schemas for comprehensive Kafka MCP API
class TopicMetadataResponse(BaseModel):
    success: bool = Field(..., description="Whether the request was successful")
    topic: str = Field(..., description="Topic name")
    metadata: Dict[str, Any] = Field(..., description="Topic metadata")

class ClusterInfoResponse(BaseModel):
    success: bool = Field(..., description="Whether the request was successful")
    cluster: Dict[str, Any] = Field(..., description="Cluster information")

class TopicListResponse(BaseModel):
    success: bool = Field(..., description="Whether the request was successful")
    topics: List[str] = Field(..., description="List of topic names")
    count: int = Field(..., description="Number of topics")

class CustomerQueryRequest(BaseModel):
    query_id: Optional[str] = Field(None, description="Unique query identifier")
    customer_id: str = Field(..., description="Customer identifier")
    query_text: str = Field(..., description="Customer query text")
    priority: str = Field("normal", description="Query priority (low, normal, high, urgent)")
    category: str = Field("general", description="Query category")

class AgentResponseRequest(BaseModel):
    query_id: str = Field(..., description="Related query identifier")
    agent_id: str = Field(..., description="Agent identifier")
    response_text: str = Field(..., description="Agent response text")
    confidence: float = Field(0.8, description="Response confidence score")
    processing_time: Optional[float] = Field(None, description="Processing time in seconds")

class ConsumerRequest(BaseModel):
    topic: str = Field(..., description="Topic to consume from")
    consumer_id: str = Field(..., description="Unique consumer identifier")
    auto_commit: bool = Field(True, description="Auto-commit offsets")
    max_poll_records: int = Field(100, description="Maximum records per poll")

class ConsumerResponse(BaseModel):
    success: bool = Field(..., description="Whether the operation was successful")
    consumer_id: str = Field(..., description="Consumer identifier")
    message: str = Field(..., description="Operation result message")

class HealthCheckResponse(BaseModel):
    status: str = Field(..., description="Health status (healthy/unhealthy)")
    connected: bool = Field(..., description="Connection status")
    client_type: str = Field(..., description="Client type")
    bootstrap_servers: str = Field(..., description="Kafka bootstrap servers")
    topic_prefix: str = Field(..., description="Topic prefix")
    test_result: Optional[Dict[str, Any]] = Field(None, description="Test operation result")

class ActiveConsumersResponse(BaseModel):
    success: bool = Field(..., description="Whether the request was successful")
    active_consumers: List[str] = Field(..., description="List of active consumer IDs")
    count: int = Field(..., description="Number of active consumers")

class CustomerSupportSetupResponse(BaseModel):
    success: bool = Field(..., description="Whether setup was successful")
    message: str = Field(..., description="Setup result message")
    topics: List[str] = Field(..., description="Created topics")

class RecentQueriesResponse(BaseModel):
    success: bool = Field(..., description="Whether the request was successful")
    queries: List[Dict[str, Any]] = Field(..., description="Recent customer queries")
    count: int = Field(..., description="Number of queries")

class RecentResponsesResponse(BaseModel):
    success: bool = Field(..., description="Whether the request was successful")
    responses: List[Dict[str, Any]] = Field(..., description="Recent agent responses")
    count: int = Field(..., description="Number of responses")

# Postgres-Kafka Consumer schemas
class ConsumerStartRequest(BaseModel):
    topics: Optional[List[str]] = Field(None, description="Topics to consume from (if not specified, uses all configured topics)")

class ConsumerStartResponse(BaseModel):
    success: bool = Field(..., description="Whether the consumer started successfully")
    message: str = Field(..., description="Status message")
    topics: List[str] = Field(..., description="Topics being consumed")
    table_mappings: Dict[str, str] = Field(..., description="Topic to table mappings")

class ConsumerStatusResponse(BaseModel):
    success: bool = Field(..., description="Whether the request was successful")
    running: bool = Field(..., description="Whether the consumer is running")
    active_topics: Optional[List[str]] = Field(None, description="Currently active topics")
    messages_processed: Optional[int] = Field(None, description="Total messages processed")
    messages_failed: Optional[int] = Field(None, description="Total messages failed")
    last_processed_time: Optional[str] = Field(None, description="Last processing timestamp")
    table_mappings: Optional[Dict[str, str]] = Field(None, description="Topic to table mappings")
    message: Optional[str] = Field(None, description="Status message if not running")

class TableSetupResponse(BaseModel):
    success: bool = Field(..., description="Whether table setup was successful")
    message: str = Field(..., description="Setup result message")
    tables: List[str] = Field(..., description="Created tables")

class TestInsertResponse(BaseModel):
    success: bool = Field(..., description="Whether the test insert was successful")
    message: str = Field(..., description="Test result message")
    test_data: Dict[str, Any] = Field(..., description="Test data that was inserted")
    kafka_result: Dict[str, Any] = Field(..., description="Kafka publish result")

class DatabaseQueryResponse(BaseModel):
    success: bool = Field(..., description="Whether the query was successful")
    table: str = Field(..., description="Queried table name")
    count: int = Field(..., description="Number of records returned")
    records: List[Dict[str, Any]] = Field(..., description="Query results")
