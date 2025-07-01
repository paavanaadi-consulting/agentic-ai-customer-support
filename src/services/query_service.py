"""
Query service for handling customer query business logic.
"""
import uuid
import time
from datetime import datetime
from typing import List, Optional, Dict, Any

from ..api.schemas import (
    QueryRequest, QueryResponse, QueryType, Priority
)


class QueryService:
    """Service class for handling query-related business logic."""
    
    def __init__(self):
        # In-memory storage for demo purposes (replace with database in production)
        self.queries_db = {}
        
        # Agent mapping configuration
        self.agent_mapping = {
            QueryType.TECHNICAL: "technical_agent",
            QueryType.BILLING: "billing_agent", 
            QueryType.ACCOUNT: "account_agent",
            QueryType.COMPLAINT: "response_agent",
            QueryType.GENERAL: "general_agent"
        }
        
        # Response templates
        self.response_mapping = {
            QueryType.TECHNICAL: "Technical support response for: {}...",
            QueryType.BILLING: "Billing inquiry handled: {}...",
            QueryType.ACCOUNT: "Account information: {}...",
            QueryType.COMPLAINT: "We apologize for the inconvenience regarding: {}...",
            QueryType.GENERAL: "Thank you for your inquiry: {}..."
        }
    
    async def process_query(self, request: QueryRequest) -> QueryResponse:
        """
        Process a customer query using AI agents.
        
        Args:
            request: QueryRequest containing query details
            
        Returns:
            QueryResponse with processed results
            
        Raises:
            Exception: If query processing fails
        """
        query_id = str(uuid.uuid4())
        processing_start = time.time()
        
        try:
            # Determine which agent to use based on query type
            agent_used = self.agent_mapping.get(request.query_type, "general_agent")
            
            # Generate response based on query type
            response_template = self.response_mapping.get(
                request.query_type, 
                "Response to: {}"
            )
            result = response_template.format(request.query[:50])
            
            # Calculate processing time
            processing_time = time.time() - processing_start
            
            # Store query in database
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
                "context": request.context,
                "metadata": request.metadata
            }
            self.queries_db[query_id] = query_data
            
            # Generate suggestions based on query type
            suggestions = self._generate_suggestions(request.query_type)
            
            return QueryResponse(
                query_id=query_id,
                result=result,
                confidence=self._calculate_confidence(request),
                success=True,
                agent_used=agent_used,
                processing_time=processing_time,
                suggestions=suggestions,
                timestamp=query_data["timestamp"]
            )
            
        except Exception as e:
            # Log error and re-raise
            # In production, you'd use proper logging here
            print(f"Query processing failed: {str(e)}")
            raise e
    
    async def get_query_by_id(self, query_id: str) -> Optional[QueryResponse]:
        """
        Retrieve a query by its ID.
        
        Args:
            query_id: The unique query identifier
            
        Returns:
            QueryResponse if found, None otherwise
        """
        if query_id not in self.queries_db:
            return None
        
        query = self.queries_db[query_id]
        return QueryResponse(
            query_id=query["query_id"],
            result=query["result"],
            confidence=0.85,  # Could be stored or recalculated
            success=True,
            agent_used=query["agent_used"],
            processing_time=query["processing_time"],
            suggestions=[],
            timestamp=query["timestamp"]
        )
    
    async def list_queries(
        self, 
        customer_id: Optional[str] = None,
        query_type: Optional[QueryType] = None,
        limit: int = 10
    ) -> List[QueryResponse]:
        """
        List queries with optional filtering.
        
        Args:
            customer_id: Filter by customer ID
            query_type: Filter by query type
            limit: Maximum number of results to return
            
        Returns:
            List of QueryResponse objects
        """
        filtered_queries = list(self.queries_db.values())
        
        # Apply filters
        if customer_id:
            filtered_queries = [
                q for q in filtered_queries 
                if q["customer_id"] == customer_id
            ]
        
        if query_type:
            filtered_queries = [
                q for q in filtered_queries 
                if q["query_type"] == query_type
            ]
        
        # Apply limit
        filtered_queries = filtered_queries[:limit]
        
        # Convert to response objects
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
    
    def _generate_suggestions(self, query_type: QueryType) -> List[str]:
        """Generate contextual suggestions based on query type."""
        base_suggestions = [
            "Check our FAQ section",
            "Consider scheduling a call",
            "Review our documentation"
        ]
        
        type_specific_suggestions = {
            QueryType.TECHNICAL: [
                "Check system status page",
                "Review troubleshooting guide",
                "Contact technical support"
            ],
            QueryType.BILLING: [
                "View billing history",
                "Update payment method",
                "Contact billing department"
            ],
            QueryType.ACCOUNT: [
                "Update account settings",
                "Verify account information",
                "Reset password"
            ],
            QueryType.COMPLAINT: [
                "Escalate to manager",
                "Request callback",
                "Submit formal complaint"
            ]
        }
        
        return type_specific_suggestions.get(query_type, base_suggestions)
    
    def _calculate_confidence(self, request: QueryRequest) -> float:
        """Calculate confidence score based on query characteristics."""
        base_confidence = 0.85
        
        # Adjust confidence based on query length
        if len(request.query) < 10:
            base_confidence -= 0.1
        elif len(request.query) > 100:
            base_confidence += 0.05
        
        # Adjust confidence based on context availability
        if request.context:
            base_confidence += 0.05
        
        # Adjust confidence based on query type specificity
        if request.query_type != QueryType.GENERAL:
            base_confidence += 0.05
        
        return min(0.99, max(0.5, base_confidence))
    
    def get_query_count(self) -> int:
        """Get total number of queries."""
        return len(self.queries_db)
    
    def get_queries_by_type(self) -> Dict[str, int]:
        """Get query count by type."""
        queries_by_type = {}
        for query in self.queries_db.values():
            query_type = query["query_type"].value
            queries_by_type[query_type] = queries_by_type.get(query_type, 0) + 1
        return queries_by_type
    
    def get_average_processing_time(self) -> float:
        """Calculate average query processing time."""
        if not self.queries_db:
            return 0.0
        
        total_time = sum(q["processing_time"] for q in self.queries_db.values())
        return total_time / len(self.queries_db)
